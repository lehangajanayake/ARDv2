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

NSS (SPI chip select) -> CE1 / BCM GPIO7 / physical pin 26
DIO0 (interrupt) -> BCM GPIO18 / physical pin 12
RESET -> BCM GPIO12 / physical pin 32
"""

import argparse
import asyncio
import json
import logging
import time
import traceback
from typing import Any, Optional

import websockets
from raspi_lora import LoRa, ModemConfig
from raspi_lora import constants as rlc

TELEMETRY_FIELD_COUNT = 12
TX_POWER_FLOOR = 5  # library's documented minimum; never actually used (see ReceiveOnlyLoRa)
RECEIVING_TIMEOUT_SECONDS = 10

connected_clients: set[Any] = set()
logger = logging.getLogger("lora_receiver")
received_packet_count = 0
valid_packet_count = 0
rejected_packet_count = 0
started_at = 0.0
radio_ready = False
last_valid_packet_at: Optional[float] = None


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
		"--spi-channel", type=int, default=1, choices=(0, 1),
		help="SPI channel: 0 for CE0, 1 for CE1 (whichever the inAir9B NSS pin is wired to).",
	)
	parser.add_argument(
		"--interrupt-pin", type=int, default=18,
		help="BCM GPIO pin wired to the inAir9B's DIO0 pin.",
	)
	parser.add_argument(
		"--reset-pin", type=int, default=12,
		help="BCM GPIO pin wired to the inAir9B's RESET pin, if any. "
		"raspi-lora does not drive reset itself; pass this if your board "
		"needs an active reset pulse to come up reliably.",
	)
	parser.add_argument("--address", type=int, default=1, help="Unused by this receive-only build; kept for API compatibility with the LoRa constructor.")
	parser.add_argument("--host", default="localhost")
	parser.add_argument("--websocket-port", type=int, default=8765)
	parser.add_argument(
		"--health-host", default="0.0.0.0",
		help="Interface for the HTTP health endpoint (default: all interfaces).",
	)
	parser.add_argument("--health-port", type=int, default=8080)
	parser.add_argument(
		"--mock-telemetry",
		action="store_true",
		help="Skip LoRa hardware initialization and periodically send mock SRAD telemetry.",
	)
	parser.add_argument(
		"--mock-interval",
		type=float,
		default=1.0,
		metavar="SECONDS",
		help="Seconds between mock telemetry packets (default: 1.0).",
	)
	parser.add_argument(
		"--debug",
		action="store_true",
		help="Enable detailed LoRa, packet, and WebSocket diagnostics.",
	)
	return parser.parse_args()


async def send_mock_telemetry(callback: Any, interval: float) -> None:
	"""Generate valid SRAD-shaped packets for end-to-end UI testing."""
	sequence = 0
	while True:
		packet = (
			f"{sequence},{20.0 + sequence % 5:.1f},1013.2,{100.0 + sequence:.1f},"
			"0.1,0.2,1.0,0.0,0.0,0.0,-34.429494,139.600430"
		).encode("ascii")
		callback(packet)
		sequence += 1
		await asyncio.sleep(interval)


def pulse_reset(reset_pin: int) -> None:
	"""Manually reset the SX1276 before raspi-lora talks to it.

	raspi-lora's LoRa.__init__ never touches a reset pin and asserts the
	chip responds correctly immediately after its first register write.
	If your board needs an active reset (i.e. it doesn't self-reset via an
	RC network on power-up), do it here first.
	"""
	logger.debug("Pulsing SX1276 reset pin BCM GPIO%d.", reset_pin)
	import RPi.GPIO as GPIO

	GPIO.setmode(GPIO.BCM)
	GPIO.cleanup(reset_pin)
	GPIO.setup(reset_pin, GPIO.OUT)
	try:
		GPIO.output(reset_pin, GPIO.LOW)
		time.sleep(0.01)
		GPIO.output(reset_pin, GPIO.HIGH)
		time.sleep(0.01)
	finally:
		GPIO.cleanup(reset_pin)
	logger.debug("SX1276 reset pulse complete.")


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
		global received_packet_count
		irq_flags = self._spi_read(rlc.REG_12_IRQ_FLAGS)

		if self._mode == rlc.MODE_RXCONTINUOUS and (irq_flags & rlc.RX_DONE):
			received_packet_count += 1
			packet_len = self._spi_read(rlc.REG_13_RX_NB_BYTES)
			self._spi_write(
				rlc.REG_0D_FIFO_ADDR_PTR,
				self._spi_read(rlc.REG_10_FIFO_RX_CURRENT_ADDR),
			)
			packet = self._spi_read(rlc.REG_00_FIFO, packet_len)
			self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)
			logger.debug(
				"RX packet #%d received: %d bytes.",
				received_packet_count,
				packet_len,
			)

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
		global valid_packet_count, rejected_packet_count, last_valid_packet_at
		try:
			line = packet.decode("ascii", errors="ignore").strip()
			if is_telemetry_packet(line):
				valid_packet_count += 1
				last_valid_packet_at = time.monotonic()
				logger.debug(
					"Valid telemetry packet #%d: %s",
					valid_packet_count,
					line,
				)
				loop.call_soon_threadsafe(queue.put_nowait, line)
			else:
				rejected_packet_count += 1
				logger.warning(
					"Rejected LoRa payload #%d (%d bytes): %r",
					rejected_packet_count,
					len(packet),
					line,
				)
		except Exception:
			logger.exception("Error while decoding a LoRa payload.")

	return on_telemetry


async def broadcast(message: str) -> None:
	if not connected_clients:
		logger.debug("Telemetry received with no WebSocket clients connected.")
		return
	logger.debug("Broadcasting telemetry to %d WebSocket client(s).", len(connected_clients))

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


async def handle_health_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
	"""Serve a small JSON health response over HTTP for service monitoring."""
	try:
		request = await asyncio.wait_for(reader.readline(), timeout=3)
		parts = request.decode("ascii", errors="replace").strip().split()
		request_target = parts[1].split("?", 1)[0].rstrip("/") if len(parts) >= 2 else ""
		# Consume headers so the connection can be closed cleanly.
		while await asyncio.wait_for(reader.readline(), timeout=3) not in (b"\r\n", b"\n", b""):
			pass

		if request_target != "/health":
			status, payload = "404 Not Found", {"status": "not_found"}
		elif parts[0] != "GET":
			status, payload = "405 Method Not Allowed", {"status": "method_not_allowed"}
		else:
			status = "200 OK"
			now = time.monotonic()
			last_packet_age = (
				round(now - last_valid_packet_at, 1)
				if last_valid_packet_at is not None
				else None
			)
			receiving_data = (
				radio_ready
				and last_packet_age is not None
				and last_packet_age <= RECEIVING_TIMEOUT_SECONDS
			)
			payload = {
				"service_running": True,
				"lora_connected": radio_ready,
				"receiving_data": receiving_data,
				"last_valid_packet_age_seconds": last_packet_age,
				"uptime_seconds": round(time.monotonic() - started_at, 1),
				"packets_received": received_packet_count,
				"valid_packets": valid_packet_count,
				"rejected_packets": rejected_packet_count,
				"websocket_clients": len(connected_clients),
			}
		body = json.dumps(payload).encode("utf-8")
		headers = (
			f"HTTP/1.1 {status}\r\n"
			"Content-Type: application/json; charset=utf-8\r\n"
			f"Content-Length: {len(body)}\r\n"
			"Connection: close\r\n\r\n"
		)
		writer.write(headers.encode("ascii") + body)
		await writer.drain()
	except (asyncio.TimeoutError, ConnectionError):
		pass
	finally:
		writer.close()
		try:
			await writer.wait_closed()
		except ConnectionError:
			pass


async def handle_client(websocket: Any, *_args: Any) -> None:
	"""Register a read-only telemetry client; never receive commands."""
	connected_clients.add(websocket)
	remote = getattr(websocket, "remote_address", "unknown client")
	logger.info("WebSocket client connected: %s", remote)
	try:
		await websocket.wait_closed()
	finally:
		connected_clients.discard(websocket)
		logger.info("WebSocket client disconnected: %s", remote)


async def run(arguments: argparse.Namespace) -> None:
	global started_at, radio_ready, last_valid_packet_at
	if arguments.mock_interval <= 0:
		raise ValueError("--mock-interval must be greater than zero")
	started_at = time.monotonic()
	last_valid_packet_at = None
	logger.info(
		"Starting LoRa receiver: frequency=%.3f MHz, SPI channel=%d, interrupt GPIO=%d, "
		"reset GPIO=%s, WebSocket=%s:%d",
		arguments.frequency,
		arguments.spi_channel,
		arguments.interrupt_pin,
		arguments.reset_pin if arguments.reset_pin is not None else "disabled",
		arguments.host,
		arguments.websocket_port,
	)
	if arguments.reset_pin is not None and not arguments.mock_telemetry:
		pulse_reset(arguments.reset_pin)

	loop = asyncio.get_running_loop()
	queue: "asyncio.Queue[str]" = asyncio.Queue()
	telemetry_callback = make_telemetry_callback(loop, queue)
	radio: Optional[ReceiveOnlyLoRa] = None
	mock_task: Optional[asyncio.Task[None]] = None

	if arguments.mock_telemetry:
		logger.warning("Mock telemetry enabled; skipping LoRa hardware initialization.")
		mock_task = asyncio.create_task(
			send_mock_telemetry(telemetry_callback, arguments.mock_interval)
		)
	else:
		logger.info("Initializing raspi-lora and opening SPI/GPIO.")
		try:
			radio = ReceiveOnlyLoRa(
				arguments.spi_channel,
				arguments.interrupt_pin,
				arguments.address,
				freq=arguments.frequency,
				tx_power=TX_POWER_FLOOR,
				modem_config=ModemConfig.Bw125Cr45Sf128,
				acks=False,
				on_telemetry=telemetry_callback,
			)
			logger.info("LoRa object initialized successfully.")
			version_register = getattr(rlc, "REG_42_VERSION", 0x42)
			chip_version = radio._spi_read(version_register)
			logger.info("SX127x version register 0x%02X returned 0x%02X.", version_register, chip_version)
			logger.info("Setting radio to continuous receive mode.")
			radio.set_mode_rx()
		except Exception:
			logger.exception(
				"LoRa initialization failed. Check SPI enablement, NSS/SPI channel, "
				"DIO0 interrupt GPIO, reset wiring, frequency, and power.",
			)
			raise
		logger.info(
			"LoRa receive-only radio ready at %.3f MHz; transmit is disabled at the code level in this program.",
			arguments.frequency,
		)
		radio_ready = True

	try:
		async with websockets.serve(
			handle_client,
			arguments.host,
			arguments.websocket_port,
		):
			logger.info(
				f"WebSocket telemetry server listening at "
				f"ws://{arguments.host}:{arguments.websocket_port}"
			)
			async with await asyncio.start_server(
				handle_health_request,
				arguments.health_host,
				arguments.health_port,
			):
				logger.info(
					"HTTP health endpoint listening at http://%s:%d/health",
					arguments.health_host,
					arguments.health_port,
				)
				await drain_telemetry(queue)
	finally:
		if mock_task is not None:
			mock_task.cancel()
			try:
				await mock_task
			except asyncio.CancelledError:
				pass
		radio_ready = False
		logger.info(
			"Stopping receiver. RX packets=%d, valid telemetry=%d, rejected payloads=%d.",
			received_packet_count,
			valid_packet_count,
			rejected_packet_count,
		)
		if radio is not None:
			radio.close()


def main() -> None:
	arguments = parse_arguments()
	logging.basicConfig(
		level=logging.DEBUG if arguments.debug else logging.INFO,
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
	logger.debug("Debug logging enabled.")
	try:
		asyncio.run(run(arguments))
	except KeyboardInterrupt:
		logger.info("Receiver stopped by keyboard interrupt.")
	except Exception:
		logger.exception("Receiver stopped because of an unhandled error.")
		raise


if __name__ == "__main__":
	main()
