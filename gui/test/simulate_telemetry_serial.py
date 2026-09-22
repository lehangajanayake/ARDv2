import serial
import time
import random


# SERIAL_PORT = "/dev/ttys001"  # Replace with the port created by socat
SERIAL_PORT = "/dev/ttys035"  # Replace with the port created by socat
BAUD_RATE = 115200  

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit()

# Function to generate sample telemetry data
def generate_telemetry_packet():
    return {
        "time": round(time.time(), 3),
        "bmpTemp": round(random.uniform(15, 40), 6),
        "imuTemp": round(random.uniform(15, 40), 6),
        "pressure": round(random.uniform(900, 1100), 2),
        "altitude": round(random.uniform(0, 5000), 2),
        "accX": round(random.uniform(-2, 2), 6),
        "accY": round(random.uniform(-2, 2), 6),
        "accZ": round(random.uniform(-2, 2), 6),
        "gyroX": round(random.uniform(-250, 250), 6),
        "gyroY": round(random.uniform(-250, 250), 6),
        "gyroZ": round(random.uniform(-250, 250), 6),
    }

# Send telemetry data over serial port
try:
    while True:
        packet = generate_telemetry_packet()
        
        # Format as CSV string
        csv_data = f"{packet['time']},{packet['bmpTemp']},{packet['imuTemp']},{packet['pressure']},{packet['altitude']},{packet['accX']},{packet['accY']},{packet['accZ']},{packet['gyroX']},{packet['gyroY']},{packet['gyroZ']}\n"
        
        # Write to serial port
        ser.write(csv_data.encode('utf-8'))
        print("Sent:", csv_data.strip())

        time.sleep(1)  # Send data every 1 second

except KeyboardInterrupt:
    print("\nStopping serial transmission...")
    ser.close()
