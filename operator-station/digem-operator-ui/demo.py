"""
demo.py — Presentation mode with fake live data.
Run this instead of main.py for demos.
"""

import sys
import os
import random
import time
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from main import MainWindow
from config import State

# ── Fake data config ──────────────────────────────────────────────────────────

FAKE_LOG = [
    ("COMMS",   "Relay 1 (192.168.100.10): connected"),
    ("COMMS",   "Relay 2 (192.168.100.11): connected"),
    ("COMMS",   "Teensy 1 (192.168.100.60): connected"),
    ("COMMS",   "Teensy 2 (192.168.100.61): connected"),
    ("STATE",   "System state → IDLE"),
    ("INFO",    "Pre-bore checklist complete"),
    ("CONTROL", "Relay 1 CH1 (E-Brake 1): ON"),
    ("CONTROL", "Relay 1 CH2 (E-Brake 1 GND): ON"),
    ("CONTROL", "Relay 1 CH3 (E-Brake 2): ON"),
    ("CONTROL", "Relay 1 CH4 (E-Brake 2 GND): ON"),
    ("INFO",    "E-brake valves pressurised — system ready"),
    ("STATE",   "System state → RUNNING"),
    ("INFO",    "Mining STARTED — MQTT telemetry publishing"),
    ("CONTROL", "Relay 1 CH7 (Injection Pump): ON"),
    ("CONTROL", "Relay 1 CH8 (Injection Pump): ON"),
    ("INFO",    "Injection pump online — flow nominal"),
    ("WARN",    "Roll: 12.40  [HIGH WARN]"),
    ("INFO",    "Roll: alarm/warn cleared — back to normal"),
    ("WARN",    "Encl_Temp1: 58.10  [HIGH WARN]"),
    ("ALARM",   "RPM: 1020.00  [HIGH ALARM]"),
    ("INFO",    "RPM: alarm/warn cleared — back to normal"),
    ("INFO",    "Bore depth 0.50 m reached"),
    ("INFO",    "Bore depth 1.00 m reached — minimum depth achieved"),
]

# Base sensor values (will oscillate slightly)
BASE = {
    "RPM":        15.0,
    "Flow":       11.0,
    "Depth":      0.70,
    "Roll":       0.4,
    "Pitch":      -0.3,
    "Yaw":        2.1,
    "Encl_Temp1": 44.0,
    "Encl_Temp2": 39.0,
}

BASE_POWER = {
    "relay1": (23.8, 8.2),
    "relay2": (23.9, 1.4),
    "24v":    (24.1, 3.6),
    "12v":    (11.9, 6.8),
}


class DemoRunner:

    def __init__(self, window: MainWindow):
        self.w = window

        # Seed graph history before window is visible
        self._seed_graphs()

        # Set initial UI state
        self._setup_state()

        # Stop all internal refresh/stale timers — data is static
        self.w.tab_machine._timer.stop()
        self.w.tab_power._timer.stop()
        self.w.tab_dashboard._stale_timer.stop()

        # Dump all log entries at once
        for cat, msg in FAKE_LOG:
            self.w.tab_log.log(cat, msg)

    def _setup_state(self):
        w = self.w

        # Connection dots — all green
        for dev in ["relay1", "relay2", "teensy1", "teensy2"]:
            w.topbar.update_connection(dev, True)
        w._relay1_connected = True

        # State → RUNNING
        w._set_state(State.RUNNING)

        # Controls — show relay channels on
        for ch in [1, 2, 3, 4, 7, 8]:
            w.tab_controls.set_channel(1, ch, True)
        for ch in [1, 2, 3]:
            w.tab_controls.set_channel(2, ch, True)

        # Pump indicator on
        w.tab_power.set_pump_state(True)

        # Dashboard warnings
        w.tab_dashboard.warnings.notify_connected()
        w.tab_dashboard.warnings.set_warning(
            "encl_warn", "Encl_Temp1: 44.0 — HIGH WARN", is_alarm=False
        )

        # Status bar
        w.statusBar().showMessage(
            "Mining active — MQTT publishing at 0.1 Hz  |  All systems nominal"
        )

        # Initial sensor push
        for key, val in BASE.items():
            w.tab_dashboard.update_sensor(key, val)
            w.tab_machine.update_sensor(key, val)

        # Initial power push
        for key, (v, a) in BASE_POWER.items():
            w.tab_dashboard.update_power(key, v, a)
            w.tab_power.update_power(key, v, a)

        # Mining toggle on
        w.tab_dashboard.mqtt_card._mining = True
        w.tab_dashboard.mqtt_card.mining_btn.setText("⛏  MINING: ON")
        w.tab_dashboard.mqtt_card.mining_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a4a1a;
                color: #66ff66;
                border: 2px solid #44aa44;
                border-radius: 6px;
                padding: 6px 14px;
            }
        """)

    def _seed_graphs(self):
        """Pre-fill 60s of fake history — batch all points, single redraw per graph."""
        now = time.time()
        w = self.w

        for i in range(60):
            age = 60 - i
            t_offset = now - age
            n = lambda s=1: random.gauss(0, s)

            w.tab_machine.graph_rpm._times.append(t_offset - w.tab_machine.graph_rpm._t0)
            w.tab_machine.graph_rpm._vals.append(max(0, min(20, BASE["RPM"] + n(1.2))))

            w.tab_machine.graph_flow._times.append(t_offset - w.tab_machine.graph_flow._t0)
            w.tab_machine.graph_flow._vals.append(max(0, min(20, BASE["Flow"] + n(0.5))))

            w.tab_machine.graph_depth._times.append(t_offset - w.tab_machine.graph_depth._t0)
            w.tab_machine.graph_depth._vals.append(max(0, BASE["Depth"] - age * 0.004 + n(0.005)))

            for key, (v, a) in BASE_POWER.items():
                g = w.tab_power._rail_cards[key]._graph
                g._times.append(t_offset - g._t0)
                g._vals.append(max(0, (v + n(0.1)) * (a + n(0.3))))

        # Single redraw per graph after all data is loaded
        for g in [w.tab_machine.graph_rpm, w.tab_machine.graph_flow, w.tab_machine.graph_depth]:
            g._redraw()
        for card in w.tab_power._rail_cards.values():
            card._graph._redraw()



def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DiGEM TBM Operator Station — DEMO")

    window = MainWindow()
    window.setWindowTitle("Dig 'Em Aggies — TBM Operator Station  [DEMO MODE]")
    window.show()

    demo = DemoRunner(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
