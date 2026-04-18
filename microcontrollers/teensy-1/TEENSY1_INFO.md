# Teensy 1 — Firmware Reference

## Hardware
- **Board**: Teensy 4.1
- **Role**: Sensor data acquisition
- **Serial Number**: 18378030
- **USB Port**: /dev/ttyACM0

## Network
- **IP**: 192.168.100.60
- **MAC**: DE:AD:BE:EF:FE:01
- **Gateway**: 192.168.100.1
- **Subnet**: 255.255.255.0
- **Broadcast**: 192.168.100.255
- **UDP Port**: 5000
- **Broadcast Rate**: 2 Hz (every 500ms)

## Pin Assignments
| Pin | Device | Interface | Notes |
|-----|--------|-----------|-------|
| 2 | RPM Optocoupler (NOYITO PC817) | Digital Interrupt | 12V signal conditioned to 5V |
| 3 | Flow Optocoupler (NOYITO PC817) | Digital Interrupt | 5V pulse |
| 18 (SDA) | BNO085 IMU + TF-Luna LiDAR | I2C | Shared bus |
| 19 (SCL) | BNO085 IMU + TF-Luna LiDAR | I2C | Shared bus |
| 3.3V | BNO085 VCC, TF-Luna VCC | Power | |
| GND | All sensors | Ground | |

## Sensors
| Sensor | Interface | I2C Address | Output |
|--------|-----------|-------------|--------|
| BNO085 IMU | I2C | 0x4A | Roll, Pitch, Yaw (degrees) |
| TF-Luna LiDAR | I2C | 0x10 | Bore depth (cm) |
| RPM Optocoupler | Interrupt Pin 2 | — | Cutterhead RPM |
| Flow Optocoupler | Interrupt Pin 3 | — | Flow rate (Hz) |

## Libraries
| Library | Source | Purpose |
|---------|--------|---------|
| NativeEthernet | GitHub (vjmuzik) | Teensy 4.1 built-in Ethernet |
| Adafruit BNO08x | Arduino Library Manager (v1.2.5) | BNO085 IMU |
| Adafruit BusIO | Arduino Library Manager | Adafruit BNO08x dependency |
| Adafruit Unified Sensor | Arduino Library Manager | Adafruit BNO08x dependency |

## UDP Packet Format (JSON)
```json
{
  "rpm": 12.3,
  "flow_hz": 4.5,
  "roll": 1.2,
  "pitch": -0.5,
  "yaw": 180.0,
  "depth_cm": 45.2,
  "uptime_ms": 12345
}
```

## RPM Sensor
- **Sensor**: Baomain LJC12A3-5-Z/BY capacitive proximity sensor (PNP NO, 10-30V, 1-5mm range)
- **Signal chain**: 12V proximity sensor → NOYITO PC817 optocoupler → Teensy Pin 2 (5V)
- **Target**: Metal gear rotating with cutterhead
- **Calibration**: Spin cutterhead one full revolution by hand, count pulses on serial monitor
- **Firmware constant**: `#define PULSES_PER_REV 1` — update with actual gear tooth count after calibration

## Flow Sensor
- **Sensor**: Digiten FL-608
- **Calibration**: F = 7.5 × Q (L/min) → 450 pulses/liter (factory spec)
- **Formula**: `flow_lpm = pulse_hz / 7.5`
- **Edge**: FALLING, 2ms bouncetime

## IMU Notes
- Library: Adafruit BNO08x (not SparkFun)
- Report type: SH2_GAME_ROTATION_VECTOR at 50 Hz internal
- Output: roll/pitch/yaw in **radians** (MQTT-ready, no conversion needed)
- I2C clock: 100 kHz

## Broadcast Format
- Rate: 2 Hz (every 500ms)
- Destination: 192.168.100.255:5000 (UDP broadcast)
- IMU values in radians, flow in L/min, depth in cm, RPM in rev/min

## Firmware Files
| File | Description |
|------|-------------|
| teensy1_eth_test/ | Ethernet connectivity test — static IP + link status |
| teensy1_main/ | Full sensor firmware — all sensors + UDP broadcast |

## Upload Command
```bash
arduino-cli upload --fqbn teensy:avr:teensy41 -p /dev/ttyACM0 "<sketch_path>"
```

## Compile Command
```bash
arduino-cli compile --fqbn teensy:avr:teensy41 "<sketch_path>"
```
