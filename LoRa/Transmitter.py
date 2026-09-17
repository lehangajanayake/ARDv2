import time
import math
import random
import board
import busio
import digitalio
import adafruit_rfm9x

# Define the radio frequency (Must match your hardware: 915.0 or 868.0)
RADIO_FREQ_MHZ = 915.0 

# Define pins connected to the Pi
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)

SAMPLE_INTERVAL_SECONDS = 0.25
MAP_CENTER_LAT = -30.664806
MAP_CENTER_LON = 143.196306
METERS_PER_DEGREE = 111111.0
FLIGHT_DURATION_SECONDS = 78.0
DOWNRANGE_METERS_PER_SECOND = 55.0

# Initialize the SPI bus
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

try:
    # Initialize the RFM9x radio
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
    print("RFM9x LoRa Initialized Successfully!")
except RuntimeError as error:
    print(f"Error initializing LoRa: {error}")
    print("Check your wiring and SPI interface.")
    exit()

# Optional: Adjust transmit power (5 to 23 dBm)
rfm9x.tx_power = 23

def interpolate(start_time, start_altitude, end_time, end_altitude,
                elapsed_seconds):
    progress = ((elapsed_seconds - start_time) /
                (end_time - start_time))
    return start_altitude + progress * (end_altitude - start_altitude)


def flight_altitude(elapsed_seconds):
    if elapsed_seconds <= 6.3:
        return interpolate(0.0, 0.0, 6.3, 620.0, elapsed_seconds)
    if elapsed_seconds <= 28.0:
        return interpolate(6.3, 620.0, 28.0, 3320.0, elapsed_seconds)
    if elapsed_seconds <= 42.0:
        return interpolate(28.0, 3320.0, 42.0, 2300.0, elapsed_seconds)
    return interpolate(42.0, 2300.0, FLIGHT_DURATION_SECONDS, 0.0,
                       elapsed_seconds)


def simulated_packet(time_ms, elapsed_seconds):
    elapsed_seconds = min(elapsed_seconds, FLIGHT_DURATION_SECONDS)
    altitude = flight_altitude(elapsed_seconds)
    downrange = DOWNRANGE_METERS_PER_SECOND * elapsed_seconds
    east_wind_drift = 35.0 * math.sin(elapsed_seconds * 0.35)
    north_wind_drift = 20.0 * math.sin(elapsed_seconds * 0.22 + 1.0)
    east = 0.55 * downrange + east_wind_drift
    north = 0.25 * downrange + north_wind_drift
    temperature = 25.0 - 0.0065 * altitude + random.uniform(-0.5, 0.5)
    pressure = 1013.25 * math.exp(-altitude / 8434.5)
    acc_x = random.uniform(-2.0, 2.0)
    acc_y = random.uniform(-2.0, 2.0)
    acc_z = random.uniform(8.0, 10.0)
    ang_vel_x = random.uniform(-180.0, 180.0)
    ang_vel_y = random.uniform(-180.0, 180.0)
    ang_vel_z = random.uniform(-180.0, 180.0)
    latitude = MAP_CENTER_LAT + north / METERS_PER_DEGREE
    latitude_radians = math.radians(MAP_CENTER_LAT)
    longitude = (MAP_CENTER_LON +
                 east / (METERS_PER_DEGREE * math.cos(latitude_radians)))

    return (f"{time_ms},{temperature:.3f},{pressure:.3f},{altitude:.3f},"
            f"{acc_x:.3f},{acc_y:.3f},{acc_z:.3f},{ang_vel_x:.3f},"
            f"{ang_vel_y:.3f},{ang_vel_z:.3f},{latitude:.6f},"
            f"{longitude:.6f}")


print("Transmitting simulated telemetry...")
flight_start_time = time.monotonic()
next_sample_time = flight_start_time

while True:
    now = time.monotonic()
    if now >= next_sample_time:
        elapsed_seconds = now - flight_start_time
        time_ms = int(elapsed_seconds * 1000)
        packet_text = simulated_packet(time_ms, elapsed_seconds)
        rfm9x.send(packet_text.encode("ascii"))
        print(f"Sent: {packet_text}")
        next_sample_time += SAMPLE_INTERVAL_SECONDS
    else:
        time.sleep(next_sample_time - now)