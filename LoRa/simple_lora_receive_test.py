"""Minimal receive-only test for the SX127x LoRa module."""

import time

from raspi_lora import LoRa, ModemConfig
from raspi_lora import constants as rlc

SPI_CHANNEL = 1       # CE1 / BCM GPIO7
INTERRUPT_PIN = 18    # DIO0 / BCM GPIO18
ADDRESS = 1
FREQUENCY_MHZ = 915.0


class ReceiveOnlyLoRa(LoRa):
    """Read raw packets without RadioHead headers or address filtering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        raise RuntimeError("This test is receive-only.")

    def send_to_wait(self, *args, **kwargs):
        raise RuntimeError("This test is receive-only.")

    def send_ack(self, *args, **kwargs):
        raise RuntimeError("This test is receive-only.")

    def set_mode_tx(self):
        raise RuntimeError("This test is receive-only.")

    def _handle_interrupt(self, channel):
        flags = self._spi_read(rlc.REG_12_IRQ_FLAGS)

        if self._mode != rlc.MODE_RXCONTINUOUS or not (flags & rlc.RX_DONE):
            self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)
            return

        length = self._spi_read(rlc.REG_13_RX_NB_BYTES)
        current_address = self._spi_read(rlc.REG_10_FIFO_RX_CURRENT_ADDR)
        self._spi_write(rlc.REG_0D_FIFO_ADDR_PTR, current_address)
        packet = bytes(self._spi_read(rlc.REG_00_FIFO, length))
        self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)

        print(f"Received {len(packet)} bytes")
        print(f"Raw bytes: {packet!r}")
        print(f"Text: {packet.decode('ascii', errors='replace')!r}")
        print("-" * 40)


radio = ReceiveOnlyLoRa(
    SPI_CHANNEL,
    INTERRUPT_PIN,
    ADDRESS,
    freq=FREQUENCY_MHZ,
    tx_power=5,
    modem_config=ModemConfig.Bw125Cr45Sf128,
    acks=False,
)

try:
    version = radio._spi_read(getattr(rlc, "REG_42_VERSION", 0x42))
    print(f"Radio initialized. Version register: 0x{version:02X}")
    print("Waiting for packets. Press Ctrl+C to stop.")
    radio.set_mode_rx()

    while True:
        time.sleep(1)
finally:
    radio.close()
    print("Radio closed.")
