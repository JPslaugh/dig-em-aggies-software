# NABC Raspberry Pi ROV Control + GUI

A C++ control loop for sensors/actuators with a PySide6 GUI that visualizes telemetry on macOS and Raspberry Pi. The control loop writes a local telemetry snapshot, and the GUI polls it to render a responsive dashboard.

## Project structure

- [include/](include/) — C++ headers for system components
  - [include/base.hpp](include/base.hpp) — Core interfaces
  - [include/controlSystem.hpp](include/controlSystem.hpp) — Control loop + telemetry snapshot writer
  - [include/sensors.hpp](include/sensors.hpp) — Sensor implementations
  - [include/actuators.hpp](include/actuators.hpp) — Actuator implementations
  - [include/comms.hpp](include/comms.hpp) — Communication interfaces
  - [include/safety.hpp](include/safety.hpp) — Safety monitor
  - [include/ecu.hpp](include/ecu.hpp) — ECU model
  - [include/ecu_mangr.hpp](include/ecu_mangr.hpp) — ECU manager
- [src/](src/) — C++ and Python entrypoints
  - [src/main.cpp](src/main.cpp) — System entrypoint
  - [src/gui/](src/gui/) — PySide6 GUI
    - [src/gui/app.py](src/gui/app.py) — GUI entrypoint
- [CMakeLists.txt](CMakeLists.txt) — C++ build
- [requirements.txt](requirements.txt) — Python dependencies

## Architecture

### Control loop
The C++ control loop runs at 10 Hz by default, updating ECUs, sensors, safety checks, actuators, and communications. It publishes a telemetry snapshot to a JSON file on each cycle.

Key flow:
1. Update ECU health and status.
2. Read sensors and log periodically.
3. Evaluate safety limits and interlocks.
4. Run control algorithms.
5. Update actuators.
6. Process communications.
7. Write telemetry snapshot to ./telemetry.json.

### Telemetry transport
The system currently writes telemetry to a local JSON file:
- Path: ./telemetry.json (override with ROV_TELEMETRY_PATH)
- Writer: [include/controlSystem.hpp](include/controlSystem.hpp)
- Reader: [src/gui/app.py](src/gui/app.py)

This is a low-friction, local IPC method for development. It can be swapped for UDP/TCP or a message bus if needed.

### GUI
The GUI polls the telemetry file every 200 ms and updates cards and tables for sensors/actuators, plus IMU heading.

## Build and run (macOS)

### C++ control system
From the project root:

1) Configure and build:
- cmake -S . -B build
- cmake --build build -j

2) Run:
- ./build/nabc_rov

### PySide6 GUI
In another terminal:

1) Activate the Python environment:
- source env/bin/activate

2) Install dependencies (first time only):
- pip install -r requirements.txt

3) Run the GUI:
- python3 src/gui/app.py

## Raspberry Pi notes
- Keep the GUI and control loop in separate processes to avoid blocking.
- If running headless, use X11/Wayland or a framebuffer strategy.
- Use a lower telemetry poll rate if CPU is constrained.

## Configuration
- Telemetry path: set ROV_TELEMETRY_PATH to point to a different file.
- Control loop frequency: change loopPeriod_ in [include/controlSystem.hpp](include/controlSystem.hpp).

## Troubleshooting
- If the GUI shows “Waiting for telemetry,” confirm the C++ process is running and producing telemetry.json.
- If the build fails, ensure you have Xcode command line tools installed.
