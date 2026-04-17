# Dig 'Em Aggies — TBM Software

Software repository for the Dig 'Em Aggies tunnel boring machine, competing in the Not-a-Boring Competition 2026 Digging Mini Competition.

**Team**: Dig 'Em Aggies — Texas A&M University  
**Competition**: Not-a-Boring Competition 2026, Bastrop TX  
**Category**: Digging Mini Competition

---

## Repository Structure

```
operator-station/
    digem-operator-ui/      PyQt5 operator interface for surface control
    testing-software/       Pi 5 testing and diagnostic scripts
microcontrollers/
    teensy-1/               Firmware for Teensy 4.1 unit 1 (sensors)
    teensy-2/               Firmware for Teensy 4.1 unit 2 (power monitoring)
    testing-software/       Microcontroller test sketches
archived/
    brice-gui/              Archived GUI prototype
    DEAMC_PYQT_MotorController/  Archived motor controller UI
```

---

## Operator UI

The operator UI is a PyQt5 desktop application providing real-time telemetry, relay control, and system state management for the TBM during competition.

**Features:**
- Live sensor readouts (RPM, flow, depth, orientation, temperature)
- Power rail monitoring (voltage, current, wattage)
- Manual relay channel control (password-protected)
- System state machine (E-STOPPED / IDLE / RUNNING)
- MQTT telemetry publishing for competition data submission
- Event log with category filtering and CSV/text export
- IO list compliant with NaBC 2026 Section 8d

### Running on Windows

Download the latest `DiGEM-Operator-UI.exe` from the [Releases](https://github.com/JPslaugh/dig-em-aggies-software/releases) page and run it directly — no installation required.

### Running from Source

Requires Python 3.10+.

```bash
cd operator-station/digem-operator-ui
pip install -r requirements.txt
python main.py
```

For demo mode with simulated live data:

```bash
python demo.py
```

---

## Network Configuration

| Device | IP | Role |
|---|---|---|
| Operator Laptop | 192.168.100.2 | Surface control |
| Raspberry Pi 5 (TCU) | 192.168.100.50 | Telemetry control unit |
| Relay 1 | 192.168.100.10 | Harmful devices (PNOZ S5 protected) |
| Relay 2 | 192.168.100.11 | Non-harmful devices |

---

## System Overview

The TBM control system consists of:

- **Raspberry Pi 5** — Telemetry Control Unit, runs backend services and operator UI
- **Teensy 4.1 x2** — Sensor data acquisition (IMU, LiDAR, flow, RPM, temperature) and power monitoring (INA260)
- **Waveshare 16CH Relay Boards x2** — Relay 1 for harmful devices (Modbus TCP), Relay 2 for non-harmful devices
- **Pilz PNOZ S5** — Hardware safety relay, cuts 24V to Relay 1 on E-stop
- **Operator Laptop** — Runs the operator UI over Ethernet

---

## Safety

All hardware control is subject to the PNOZ S5 safety relay. Relay 1 (harmful devices) loses power on any E-stop event regardless of software state. The operator UI enforces a software E-stop in addition to the hardware interlock.
