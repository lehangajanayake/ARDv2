import struct
import time

from raspi_lora import LoRa, ModemConfig
from raspi_lora import constants as rlc

# Hardware Pin Configuration (Adjust if needed for your Pi HAT/wiring)
SPI_CHANNEL = 1       # CE1 (GPIO 7). Use 0 if wired to CE0 (GPIO 8)
INTERRUPT_PIN = 18    # DIO0 (BCM GPIO 18)
ADDRESS = 1
FREQUENCY_MHZ = 915.0

# Struct: < (Little-Endian, packed)
# B=uint8 (header), I=uint32 (pkt_num), I=uint32 (timestamp)
# 3b=int8[3] (h3lis), 3f=float[3] (imu_accel), 3f=float[3] (imu_gyro)
# 3f=float[3] (temp, press, alt), H=uint16 (checksum)
PACKET_FORMAT = "<BII3b3f3f3fH"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)  # 50 bytes
PACKET_MAGIC = 0xAA


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
        try:
            flags = self._spi_read(rlc.REG_12_IRQ_FLAGS)

            # Check if this is an RX_DONE interrupt
            if not (flags & rlc.RX_DONE):
                self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)
                return

            # Check for Payload CRC Error (Bit 5 = 0x20)
            if flags & 0x20:
                print("[WARNING] Packet dropped due to CRC error (noise or RF saturation)!")
                self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)
                return

            # Read packet length and location in FIFO
            length = self._spi_read(rlc.REG_13_RX_NB_BYTES)
            current_address = self._spi_read(rlc.REG_10_FIFO_RX_CURRENT_ADDR)
            self._spi_write(rlc.REG_0D_FIFO_ADDR_PTR, current_address)

            # Burst-read packet payload
            raw_data = self._spi_read(rlc.REG_00_FIFO, length)
            packet = bytes(raw_data)

            # Read packet RSSI and SNR
            # For SX1276 HF port (868/915 MHz), RSSI [dBm] = -157 + RegPktRssiValue
            raw_rssi = self._spi_read(rlc.REG_1A_PKT_RSSI_VALUE)
            packet_rssi = raw_rssi - 157
            raw_snr = self._spi_read(rlc.REG_19_PKT_SNR_VALUE)
            packet_snr = (raw_snr - 256 if raw_snr > 127 else raw_snr) * 0.25

            # Clear all IRQ flags so next packet can be received
            self._spi_write(rlc.REG_12_IRQ_FLAGS, 0xFF)

            print(f"\n[RX] Received {len(packet)} bytes | RSSI: {packet_rssi} dBm | SNR: {packet_snr:.1f} dB")

            if len(packet) != PACKET_SIZE:
                print(f"  [ERROR] Expected {PACKET_SIZE} bytes, got {len(packet)} bytes (Raw: {packet!r})")
                return

            values = struct.unpack(PACKET_FORMAT, packet)
            header, packet_num, timestamp_ms = values[:3]
            accel_h3lis = values[3:6]
            imu_accel = values[6:9]
            imu_gyro = values[9:12]
            temperature_c, pressure_hpa, altitude_m, checksum = values[12:]

            if header != PACKET_MAGIC:
                print(f"  [ERROR] Invalid header 0x{header:02X} (Expected 0x{PACKET_MAGIC:02X})")
                return

            print(f"  Pkt #{packet_num:<5} | Time: {timestamp_ms} ms")
            print(f"  Altitude:     {altitude_m:.1f} m")
            print(f"  Temperature:  {temperature_c:.2f} °C")
            print(f"  Pressure:     {pressure_hpa:.2f} hPa")
            print(f"  IMU Accel(g): X={imu_accel[0]:+.2f}  Y={imu_accel[1]:+.2f}  Z={imu_accel[2]:+.2f}")
            print(f"  IMU Gyro(°/s):X={imu_gyro[0]:+.2f}  Y={imu_gyro[1]:+.2f}  Z={imu_gyro[2]:+.2f}")
            print(f"  H3LIS Accel:  {accel_h3lis}")
            print(f"  Checksum:     0x{checksum:04X}")
            print("-" * 50)

        except Exception as e:
            print(f"[EXCEPTION in IRQ handler]: {e}")


# Initialize radio
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
    print(f"Radio initialized. Version register: 0x{version:02X} (Expected 0x12)")

    # Explicitly ensure Sync Word is 0x12 (matches STM32)
    radio._spi_write(0x39, 0x12)

    radio.set_mode_rx()
    print("Listening in continuous receive mode. Press Ctrl+C to stop.\n")

    while True:
        time.sleep(1)
finally:
    radio.close()
    print("Radio closed.")