"""Receive LoRa telemetry on a Raspberry Pi and publish it over WebSocket.

Uses the `raspi-lora` library (pip install raspi-lora==0.2) for interrupt-driven
SPI/GPIO handling instead of polling. See the audit notes in the chat for why
this file overrides several of the library's internals:

  - `_handle_interrupt` is overridden to read the raw LoRa payload with no
    RadioHead 4-byte header stripped off, and no address filtering. The
    stock library assumes a RadioHead-framed transmitter; this project's
    ESP32 sender writes plain ASCII CSV telemetry, so the stock framing
    would corrupt/drop every packet.
  - `send`, `send_to_wait`, `send_ack`, and `set_mode_tx` are overridden to
    raise. This is a structural (code-level) guarantee that this process
    can never key the transmitter, independent of the `tx_power` setting.
  - `tx_power` is still pinned to the library's documented minimum (5) as
    a defensive floor, in case those overrides are ever removed.

SAFETY NOTE ON THE ANTENNA CONCERN: receiving does not stress the power
amplifier the way transmitting without a matched antenna load can. The
protection that matters here is "this process never transmits," which is
enforced above at the code level, not the RF-matching state of the antenna.
Verify this reasoning against the SX1276 datasheet / your module's app
notes if you're not comfortable taking it on faith.

Requires: pip install raspi-lora==0.2 websockets
(Pinned because this file reaches into the library's non-public
 `_spi_read`/`_spi_write`/`_handle_interrupt`/constants, which could change
 in a future release.)
"""

"""PIN CONNECTIONS

NSS (SPI chip select) -> CE0 or CE1 (CE1 (26 GPIO-phyiscal pin))
DIO0 (interrupt) -> --interrupt-pin (default 12)
//no RESET pin used
"""

import argparse
import asyncio
import time
import traceback
from typing import Any, Optional

import websockets
from raspi_lora import LoRa, ModemConfig
from raspi_lora import constants as rlc

TELEMETRY_FIELD_COUNT = 12
TX_POWER_FLOOR = 5  # library's documented minimum; never actually used (see ReceiveOnlyLoRa)

connected_clients: set[Any] = set()


def is_telemetry_packet(line: str) -> bool:
	"""Return whether a line has the ESP32 telemetry packet shape."""
	fields = line.strip().split(",")
	if len(fields) != TELEMETRY_FIELD_COUNT:
		return False

	try:
		for field in fields:
			float(field)
	except ValueError:
		return False
	return True


def parse_arguments() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Receive LoRa telemetry on a Raspberry Pi and serve it over WebSocket."
	)
	parser.add_argument("--frequency", type=float, default=915.0)
	parser.add_argument(
		"--spi-channel", type=int, default=0, choices=(0, 1),
		help="SPI channel: 0 for CE0, 1 for CE1 (whichever the inAir9B NSS pin is wired to).",
	)
	parser.add_argument(
		"--interrupt-pin", type=int, default=12,
		help="BCM GPIO pin wired to the inAir9B's DIO0 pin.",
	)
	parser.add_argument(
		"--reset-pin", type=int, default=None,
		help="BCM GPIO pin wired to the inAir9B's RESET pin, if any. "
		"raspi-lora does not drive reset itself; pass this if your board "
		"needs an active reset pulse to come up reliably.",
	)
	parser.add_argument("--address", type=int, default=1, help="Unused by this receive-only build; kept for API compatibility with the LoRa constructor.")
	parser.add_argument("--host", default="localhost")
	parser.add_argument("--websocket-port", type=int, default=8765)
	return parser.parse_args()


def pulse_reset(reset_pin: int) -> None:
	"""Manually reset the SX1276 before raspi-lora talks to it.

	raspi-lora's LoRa.__init__ never touches a reset pin and asserts the
	chip responds correctly immediately after its first register write.
	If your board needs an active reset (i.e. it doesn't self-reset via an
	RC network on power-up), do it here first.
	"""
	import RPi.GPIO as GPIO

	GPIO.setmode(GPIO.BCM)
	GPIO.setup(reset_pin, GPIO.OUT)
	GPIO.output(reset_pin, GPIO.LOW)
	time.sleep(0.01)
	GPIO.output(reset_pin, GPIO.HIGH)
	time.sleep(0.01)


class ReceiveOnlyLoRa(LoRa):
	"""raspi-lora subclass that can only ever receive.

	Transmit-capable methods are overridden to raise. The interrupt handler
	is overridden to bypass the stock library's RadioHead header framing,
	address filtering, and auto-ACK behavior, none of which apply to this
	project's raw ASCII-CSV ESP32 sender.
	"""

	def __init__(self, *args: Any, on_telemetry: Any = None, **kwargs: Any) -> None:
		self._on_telemetry = on_telemetry
		super().__init__(*args, **kwargs)

	# --- Transmit is structurally unreachable, regardless of caller ---
	def send(self, *args: Any, **kwargs: Any) -> None:
		raise RuntimeError("Transmit is disabled in this receive-only build.")

	def send_to_wait(self, *args: Any, **kwargs: Any) -> None:
		raise RuntimeError("Transmit is disabled in this receive-only build.")

	def send_ack(self, *args: Any, **kwargs: Any) -> None:
		raise RuntimeError("Transmit is disabled in this receive-only build.")

	def set_mode_tx(self) -> None:
		raise RuntimeError("Transmit is disabled in this receive-only build.")

	# --- Raw receive path: no RadioHead header, no address filter, no ACKs ---
	def _handle_interrupt(self, channel: int) -> None:
		irq_flags = self._spi_read(rlc.REG_12_IRQ_FLAGS)

		if self._mode == rlc.MODE_RXCONTINUOUS and (irq_flags & rlc.RX_DONE):
			packet_len = self._spi_read(rlc.REG_13_RX_NB_BYTES)
			self._spi_write(
				rlc.REG_0D_FIFO_ADDR_PTR,
				self._spi_read(rlc.REG_10_FIFO_RX_CURRENT_ADDR),
			)
			packet = self._spi_read(rlc.REG_00_FIFO, packet_len)
			self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)

			if self._on_telemetry is not None:
				self._on_telemetry(bytes(packet))
			return

		self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)


def make_telemetry_callback(loop: asyncio.AbstractEventLoop, queue: "asyncio.Queue[str]"):
	"""Build the callback raspi-lora invokes from its GPIO interrupt thread.

	This runs on a non-asyncio thread (RPi.GPIO's event-detect thread), so
	it must hand off to the event loop with call_soon_threadsafe rather
	than calling any asyncio API directly.
	"""

	def on_telemetry(packet: bytes) -> None:
		try:
			line = packet.decode("ascii", errors="ignore").strip()
			if is_telemetry_packet(line):
				loop.call_soon_threadsafe(queue.put_nowait, line)
		except Exception:
			traceback.print_exc()

	return on_telemetry


async def broadcast(message: str) -> None:
	if not connected_clients:
		return

	results = await asyncio.gather(
		*(client.send(message) for client in connected_clients),
		return_exceptions=True,
	)
	disconnected = {
		client
		for client, result in zip(connected_clients, results)
		if isinstance(result, Exception)
	}
	connected_clients.difference_update(disconnected)


async def drain_telemetry(queue: "asyncio.Queue[str]") -> None:
	"""Consume decoded telemetry lines handed off from the interrupt thread."""
	while True:
		line = await queue.get()
		await broadcast(line)


async def handle_client(websocket: Any, *_args: Any) -> None:
	"""Register a read-only telemetry client; never receive commands."""
	connected_clients.add(websocket)
	remote = getattr(websocket, "remote_address", "unknown client")
	print(f"WebSocket client connected: {remote}")
	try:
		await websocket.wait_closed()
	finally:
		connected_clients.discard(websocket)
		print(f"WebSocket client disconnected: {remote}")


async def run(arguments: argparse.Namespace) -> None:
	if arguments.reset_pin is not None:
		pulse_reset(arguments.reset_pin)

	loop = asyncio.get_running_loop()
	queue: "asyncio.Queue[str]" = asyncio.Queue()

	radio = ReceiveOnlyLoRa(
		arguments.spi_channel,
		arguments.interrupt_pin,
		arguments.address,
		freq=arguments.frequency,
		tx_power=TX_POWER_FLOOR,
		modem_config=ModemConfig.Bw125Cr45Sf128,  # 125 kHz, 4/5 coding, SF7 (matches original config)
		acks=False,  # belt-and-suspenders: even though send_ack() is overridden to raise
		on_telemetry=make_telemetry_callback(loop, queue),
	)
	radio.set_mode_rx()
	print(
		f"LoRa receive-only radio ready at {arguments.frequency} MHz; "
		"transmit is disabled at the code level in this program."
	)

	try:
		async with websockets.serve(
			handle_client,
			arguments.host,
			arguments.websocket_port,
		):
			print(
				f"WebSocket telemetry server listening at "
				f"ws://{arguments.host}:{arguments.websocket_port}"
			)
			await drain_telemetry(queue)
	finally:
		radio.close()


def main() -> None:
	arguments = parse_arguments()
	try:
		asyncio.run(run(arguments))
	except KeyboardInterrupt:
		print("\nReceiver stopped.")
	except Exception:
		traceback.print_exc()


if __name__ == "__main__":
	main()