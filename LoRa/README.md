# Raspberry Pi LoRa Receiver

This folder contains the receive-only Raspberry Pi firmware for the inAir9B LoRa module. It receives numeric 12-field telemetry packets and publishes valid packets to WebSocket clients.

The receiver does not transmit LoRa packets and does not accept commands from WebSocket clients.

## Hardware wiring

Use the Raspberry Pi 3.3 V pins only.

| inAir9B | Raspberry Pi |
| --- | --- |
| SCK | GPIO11 / physical pin 23 |
| MISO | GPIO9 / physical pin 21 |
| MOSI | GPIO10 / physical pin 19 |
| NSS / CS | CE1 / BCM GPIO7 / physical pin 26 |
| DIO0 | BCM GPIO18 / physical pin 12 |
| RESET | Not required by default |
| 3.3V | 3.3V / physical pin 1 |
| GND | GND |

The `NSS` connection must match the SPI channel passed to the program. The default is SPI channel `1` (CE1). The `DIO0` connection must match `--interrupt-pin`.

Keep the LoRa antenna connected whenever the radio is operating.

## Enable SPI

On the Raspberry Pi, run:

```bash
sudo raspi-config
```

Select **Interface Options**, then enable **SPI**. Reboot if requested.

## Install dependencies

From the repository root:

```bash
cd LoRa
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install adafruit-blinka spidev raspi-lora==0.2 websockets
```

Activate the environment again whenever opening a new shell:

```bash
cd LoRa
source .venv/bin/activate
```

## Run the receiver

The normal command does not use a reset pin:

```bash
python Lora_receiver_firmware.py
```

The default configuration is:

- Frequency: `915 MHz`
- SPI channel: `1` / CE1
- DIO0 interrupt: BCM GPIO `18` / physical pin 12
- WebSocket host: `localhost`
- WebSocket port: `8765`

The WebSocket endpoint is:

```text
ws://localhost:8765
```

The HTTP health endpoint is available at:

```text
http://localhost:8080/health
```

When the frontend runs on another device, the health listener binds to all
interfaces by default, so use `http://RASPBERRY_PI_IP:8080/health`. It returns
HTTP `200` with JSON while the radio and receiver are ready, or `503` while
starting or stopping. The response includes uptime, received/valid/rejected
packet counts, and the number of connected WebSocket clients. Change its bind
address or port with `--health-host` and `--health-port`.

## Run with debug logging

Use debug mode when checking radio initialization, SPI wiring, interrupt activity, or packet validation:

```bash
python Lora_receiver_firmware.py --debug
```

The logs report radio initialization, the SX127x version-register read, receive-mode setup, received packet counts, rejected payloads, WebSocket clients, and shutdown statistics.

## Connecting from another computer

If the GUI is running on another computer, listen on all interfaces:

```bash
python Lora_receiver_firmware.py --host 0.0.0.0
```

Then configure the GUI WebSocket URL with the Raspberry Pi's address:

```text
ws://RASPBERRY_PI_IP:8765
```

For example:

```text
ws://192.168.1.50:8765
```

Make sure port `8765` is reachable through the Raspberry Pi firewall and that both devices are on the same network.

## Optional hardware reset

A reset pin is not needed when the module initializes correctly after power-up. Do not pass this option unless the inAir9B RESET line is physically wired to the specified BCM GPIO.

If RESET is wired to BCM GPIO25 and the radio needs a manual reset pulse:

```bash
python Lora_receiver_firmware.py --reset-pin 25 --debug
```

## Changing the radio settings

The transmitter and receiver must use matching radio settings. To use a different frequency:

```bash
python Lora_receiver_firmware.py --frequency 868 --debug
```

If NSS is wired to CE1 instead of CE0:

```bash
python Lora_receiver_firmware.py --spi-channel 1 --debug
```

If DIO0 is wired to another BCM GPIO:

```bash
python Lora_receiver_firmware.py --interrupt-pin 17 --debug
```

## Troubleshooting

- **Initialization fails:** check that SPI is enabled, the 3.3 V and GND connections are correct, and NSS matches `--spi-channel`.
- **The version register cannot be read:** check SPI wiring and chip select first.
- **Initialization succeeds but no packets arrive:** check DIO0 wiring, the transmitter frequency, modem settings, antenna, and transmitter output format.
- **Packets are rejected:** the receiver expects exactly 12 comma-separated numeric fields.
- **The GUI cannot connect:** confirm the receiver is running, use the correct Raspberry Pi IP address, and check that port `8765` is open.

Stop the receiver with `Ctrl+C`.
