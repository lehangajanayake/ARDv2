"""Minimal receive-only test for the SX127x LoRa module."""

import struct
import time

from raspi_lora import LoRa, ModemConfig
from raspi_lora import constants as rlc

SPI_CHANNEL = 1       # CE1 / BCM GPIO7
INTERRUPT_PIN = 18    # DIO0 / BCM GPIO18
ADDRESS = 1
FREQUENCY_MHZ = 915.0
PACKET_FORMAT = "<BII3b3f3f3fH"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
PACKET_MAGIC = 0xAA
CRC_ENABLE_MASK = 0x04  # RegModemConfig2 bit 2


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

        if len(packet) != PACKET_SIZE:
            print(f"Ignoring packet: expected {PACKET_SIZE} bytes")
            print("-" * 40)
            return

        values = struct.unpack(PACKET_FORMAT, packet)
        header, packet_num, timestamp_ms = values[:3]
        accel_h3lis = values[3:6]
        imu_accel = values[6:9]
        imu_gyro = values[9:12]
        temperature_c, pressure_hpa, altitude_m, checksum = values[12:]

        if header != PACKET_MAGIC:
            print(f"Ignoring packet: expected header 0x{PACKET_MAGIC:02X}, got 0x{header:02X}")
            print("-" * 40)
            return

        print("Decoded telemetry:")
        print(f"  header:        0x{header:02X}")
        print(f"  packet_num:    {packet_num}")
        print(f"  timestamp_ms:  {timestamp_ms}")
        print(f"  h3lis_accel:   {accel_h3lis}")
        print(f"  imu_accel:     {imu_accel}")
        print(f"  imu_gyro:      {imu_gyro}")
        print(f"  temperature_C: {temperature_c:.2f}")
        print(f"  pressure_hPa:  {pressure_hpa:.2f}")
        print(f"  altitude_m:    {altitude_m:.2f}")
        print(f"  checksum:      0x{checksum:04X}")
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
    modem_config_2_register = getattr(rlc, "REG_1E_MODEM_CONFIG_2", 0x1E)
    modem_config_2 = radio._spi_read(modem_config_2_register)
    radio._spi_write(modem_config_2_register, modem_config_2 | CRC_ENABLE_MASK)
    print("CRC enabled to match the ESP32 sender")
    print("Waiting for packets. Press Ctrl+C to stop.")
    radio.set_mode_rx()

    while True:
        time.sleep(1)
finally:
    radio.close()
    print("Radio closed.")
