import time
import spidev
import board
import digitalio

spi = spidev.SpiDev()
spi.open(0, 0)              # CS = CE0, physical pin 24
spi.max_speed_hz = 500000
spi.mode = 0

reset = digitalio.DigitalInOut(board.D25)  # RESET = GPIO25, pin 22
reset.direction = digitalio.Direction.OUTPUT

def read_version():
    return spi.xfer2([0x42, 0x00])[1]

print("Before reset:", hex(read_version()))

reset.value = False
time.sleep(0.1)
print("While reset low:", hex(read_version()))

reset.value = True
time.sleep(0.1)
print("After reset:", hex(read_version()))

reset.deinit()
spi.close()
