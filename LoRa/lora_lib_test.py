import traceback
import board
import busio
import digitalio
import adafruit_rfm9x

try:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.CE0)
    reset = digitalio.DigitalInOut(board.D25)

    radio = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)
    print("RFM9x initialized successfully")
except Exception:
    traceback.print_exc()
PY