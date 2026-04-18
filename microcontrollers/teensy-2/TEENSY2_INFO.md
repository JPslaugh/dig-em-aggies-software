# Teensy 2 — Firmware Reference

## Hardware
- **Board**: Teensy 4.1
- **Role**: Power monitoring and temperature sensing

## Network
- **IP**: 192.168.100.61
- **MAC**: DE:AD:BE:EF:FE:02
- **Gateway**: 192.168.100.1
- **Subnet**: 255.255.255.0
- **Broadcast**: 192.168.100.255
- **UDP Port**: 5001
- **Broadcast Rate**: 1 Hz (every 1000ms)

## Pin Assignments
| Pin | Device | Interface | Notes |
|-----|--------|-----------|-------|
| 4 | DS18B20 Temp #1 + #2 | 1-Wire | 4.7kΩ pullup to 3.3V, both on same wire |
| 18 (SDA) | INA260 x4 | I2C | Shared bus |
| 19 (SCL) | INA260 x4 | I2C | Shared bus |
| 3.3V | INA260 VCC x4, DS18B20 VCC | Power | |
| GND | All sensors | Ground | |

## Sensors
| Sensor | Interface | I2C Address | Rail Monitored |
|--------|-----------|-------------|----------------|
| INA260 #1 | I2C | 0x40 | Relay 1 24V rail |
| INA260 #2 | I2C | 0x41 | Relay 2 24V rail |
| INA260 #3 | I2C | 0x44 | Main 24V supply |
| INA260 #4 | I2C | 0x45 | Main 12V supply |
| DS18B20 #1 | 1-Wire Pin 4 | — | Enclosure temp |
| DS18B20 #2 | 1-Wire Pin 4 | — | Enclosure temp |

## INA260 Address Config
| Sensor | A0 | A1 |
|--------|----|----|
| 0x40 (Relay 1) | GND | GND |
| 0x41 (Relay 2) | VCC | GND |
| 0x44 (24V rail) | GND | VCC |
| 0x45 (12V rail) | VCC | VCC |

## Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| NativeEthernet | GitHub (vjmuzik) | Teensy 4.1 built-in Ethernet |
| Adafruit INA260 | v1.5.3 | INA260 power monitors |
| Adafruit BusIO | v1.17.4 | Adafruit INA260 dependency |
| OneWire | v2.3.8 | DS18B20 1-Wire bus |
| DallasTemperature | v4.0.6 | DS18B20 temperature reading |

## UDP Packet Format (JSON)
```json
{
  "ina_relay1_v": 24.10,
  "ina_relay1_a": 0.500,
  "ina_relay1_w": 12.05,
  "ina_relay2_v": 24.00,
  "ina_relay2_a": 0.300,
  "ina_relay2_w": 7.20,
  "ina_24v_v": 24.20,
  "ina_24v_a": 1.200,
  "ina_24v_w": 29.04,
  "ina_12v_v": 12.10,
  "ina_12v_a": 0.800,
  "ina_12v_w": 9.68,
  "temp1_c": 25.30,
  "temp2_c": 26.10,
  "uptime_ms": 12345
}
```
- Voltage in V, current in A, power in W, temperature in °C
- Unresponsive sensor returns -1.0 (INA260) or -127.0 (DS18B20)

## Firmware Files
| File | Description |
|------|-------------|
| teensy2_main/ | Full power monitoring firmware — INA260 x4, DS18B20 x2, UDP broadcast |

## Upload Command
```bash
arduino-cli upload --fqbn teensy:avr:teensy41 -p /dev/ttyACM0 "<sketch_path>"
```

## Compile Command
```bash
arduino-cli compile --fqbn teensy:avr:teensy41 "<sketch_path>"
```
