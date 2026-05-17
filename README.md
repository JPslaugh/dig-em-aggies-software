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

### Prerequisites

- Python 3.10+ — download from [python.org](https://python.org)
- Git — download from [git-scm.com](https://git-scm.com)

### Download

```bash
git clone https://github.com/JPslaugh/dig-em-aggies-software.git
cd dig-em-aggies-software/operator-station/digem-operator-ui
```

### Windows

1. Install Python 3.10+ from [python.org](https://python.org) — check **"Add Python to PATH"** during install
2. Clone or download the repo
3. Open the `operator-station/digem-operator-ui/` folder
4. Double-click **`run_windows.bat`** — installs dependencies and launches automatically

### macOS

```bash
bash run_mac.sh
```

### Linux

```bash
bash run_linux.sh
```

### Demo Mode (no TBM hardware required)

Runs with simulated live data — useful for testing the UI off-site:

```bash
# Windows
python demo.py

# macOS / Linux
python3 demo.py
```

---

## Communication Protocol

| Link | Protocol | Notes |
|---|---|---|
| Operator UI → Relay 1 | Modbus TCP | Port 502 |
| Operator UI → Relay 2 | Modbus TCP | Port 502 |
| Teensy 1 → Pi / UI | UDP | Teensy broadcasts sensor JSON packets |
| Teensy 2 → Pi / UI | UDP | Teensy broadcasts power monitoring JSON packets |
| UI → MQTT Broker | MQTT | Competition telemetry at 0.1 Hz, broker provided at competition |

Teensy firmware is uploaded via USB. At runtime the Teensys communicate over Ethernet via UDP broadcasts. The relay boards use Modbus TCP.

---

## Network Configuration

Network IPs are configured in `operator-station/digem-operator-ui/config.py`. Update the `NETWORK` block to match your deployment before running.

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
