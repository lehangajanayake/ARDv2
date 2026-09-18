import sys
import time

import board
import busio
import digitalio
import spidev
import adafruit_rfm9x

RADIO_FREQ_MHZ = 915.0
SPI_BUS = 0
SPI_DEVICE = 0  # CE0, physical pin 24
RESET_PIN = board.D25  # GPIO25, physical pin 22


def read_registers():
    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEVICE)
    spi.max_speed_hz = 500000
    spi.mode = 0

    try:
        print("Raw SPI register test:")
        for address in (0x01, 0x06, 0x07, 0x42):
            value = spi.xfer2([address & 0x7F, 0x00])[1]
            print(f"  Register 0x{address:02X}: 0x{value:02X}")

        version = spi.xfer2([0x42, 0x00])[1]
        if version != 0x12:
            raise RuntimeError(
                f"Unexpected RFM9x version 0x{version:02X}; expected 0x12"
            )
        print("  RFM9x version 0x12 detected")
    finally:
        spi.close()


def initialize_radio():
    print("\nAdafruit RFM9x initialization test:")
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.CE0)
    reset = digitalio.DigitalInOut(RESET_PIN)

    try:
        radio = adafruit_rfm9x.RFM9x(
            spi, cs, reset, RADIO_FREQ_MHZ
        )
        print("  RFM9x initialized successfully")
        print(f"  Frequency: {RADIO_FREQ_MHZ} MHz")
        return radio
    finally:
        cs.deinit()
        reset.deinit()


try:
    read_registers()
    initialize_radio()
    print("\nLoRa hardware test passed")
except Exception as error:
    print(f"\nLoRa hardware test failed: {error}")
    sys.exit(1)
