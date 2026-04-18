import sys
import os
import traceback
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

def _excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    with open("/tmp/ui_crash.txt", "w") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
sys.excepthook = _excepthook

import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QDialog, QLineEdit, QDialogButtonBox,
    QFrame, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap

from config import State, CONTROLS_PASSWORD, NETWORK, STALE_TIMEOUT
from dashboard import DashboardTab
from machine_state import MachineStateTab
from power_tab import PowerTab
from controls_tab import ControlsTab
from log_tab import LogTab
from mqtt_publisher import MQTTPublisher
from io_list_tab import IOListTab
from udp_listener import UDPListener

# ── Dark maroon theme palette ─────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a0000;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
QTabWidget::pane {
    border: 1px solid #7a1515;
    background-color: #1a0000;
}
QTabBar::tab {
    background-color: #500000;
    color: #ffffff;
    padding: 10px 24px;
    border: 1px solid #7a1515;
    border-bottom: none;
    font-size: 14px;
    font-weight: bold;
    min-width: 130px;
}
QTabBar::tab:selected {
    background-color: #1a0000;
    color: #ffffff;
    border-bottom: 2px solid #cc2222;
}
QTabBar::tab:hover:!selected {
    background-color: #6a0000;
    color: #ffffff;
}
QPushButton {
    background-color: #500000;
    color: #ffffff;
    border: 1px solid #7a1515;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #6a0000;
    border-color: #cc0000;
}
QPushButton:pressed {
    background-color: #3a0000;
}
QPushButton:disabled {
    background-color: #2a0000;
    color: #806060;
}
QLineEdit {
    background-color: #500000;
    color: #ffffff;
    border: 1px solid #7a1515;
    border-radius: 4px;
    padding: 6px;
    font-size: 14px;
}
QLabel {
    color: #ffffff;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #800000;
}
"""

# ── Password dialog ───────────────────────────────────────────────────────────
class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Controls Access")
        self.setFixedSize(320, 150)
        self.setStyleSheet(DARK_STYLE + """
            QDialog { background-color: #1a0a0a; border: 1px solid #cc2222; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("Enter password to access Controls:")
        lbl.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl)

        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setPlaceholderText("Password")
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("QPushButton { min-width: 80px; }")
        layout.addWidget(buttons)

    def password(self):
        return self.input.text()


# ── Connection status indicator ───────────────────────────────────────────────
class ConnectionDot(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        self.dot = QLabel("●")
        self.dot.setFont(QFont("Segoe UI", 11))
        self.dot.setStyleSheet("color: #555555; background: transparent;")
        layout.addWidget(self.dot)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet("color: #cccccc; background: transparent;")
        layout.addWidget(lbl)

    def set_connected(self, connected: bool, stale: bool = False):
        if stale:
            self.dot.setStyleSheet("color: #c8820a; background: transparent;")
        elif connected:
            self.dot.setStyleSheet("color: #4caf50; background: transparent;")
        else:
            self.dot.setStyleSheet("color: #cc2222; background: transparent;")


# ── System state badge ────────────────────────────────────────────────────────
class StateBadge(QLabel):
    STATE_COLORS = {
        State.ESTOPPED: "#cc2222",
        State.IDLE:     "#c8820a",
        State.STARTING: "#4a7fc4",
        State.RUNNING:  "#4caf50",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(160)
        self.setFixedHeight(36)
        self.set_state(State.ESTOPPED)

    def set_state(self, state: str):
        color = self.STATE_COLORS.get(state, "#888888")
        self.setText(state)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                color: {color};
                border: 2px solid {color};
                border-radius: 6px;
                padding: 2px 8px;
            }}
        """)


# ── Soft stop button (cuts all relay channels via Modbus, does NOT cut power) ──
class SoftStopButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("ALL OUTPUTS OFF", parent)
        self.setFixedSize(170, 44)
        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.setToolTip(
            "Turns off all relay channels via software.\n"
            "Does NOT cut physical power — use the physical E-stop for emergencies."
        )
        self.setStyleSheet("""
            QPushButton {
                background-color: #7a1010;
                color: #ffffff;
                border: 2px solid #cc2222;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #9a1818;
                border-color: #ff4444;
            }
            QPushButton:pressed {
                background-color: #550a0a;
            }
        """)


# ── Top bar ───────────────────────────────────────────────────────────────────
class TopBar(QWidget):
    estop_triggered  = pyqtSignal()
    reset_triggered  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet("background-color: #3a0000; border-bottom: 2px solid #7a1515;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(0)

        # Logo — use PNG if available, fall back to text
        _logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.isfile(_logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(_logo_path)
            logo_lbl.setPixmap(pix.scaledToHeight(48, Qt.SmoothTransformation))
            logo_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            logo_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(logo_lbl)
        else:
            title = QLabel("Dig 'Em Aggies — TBM Operator Station")
            title.setFont(QFont("Segoe UI", 13, QFont.Bold))
            title.setStyleSheet("color: #ffffff; background: transparent;")
            layout.addWidget(title)

        layout.addStretch()

        # Connection dots — grouped tightly
        self.conn_relay1  = ConnectionDot("Relay 1")
        self.conn_relay2  = ConnectionDot("Relay 2")
        self.conn_teensy1 = ConnectionDot("Teensy 1")
        self.conn_teensy2 = ConnectionDot("Teensy 2")
        for dot in [self.conn_relay1, self.conn_relay2, self.conn_teensy1, self.conn_teensy2]:
            layout.addWidget(dot)

        layout.addSpacing(16)

        # State badge
        self.state_badge = StateBadge()
        layout.addWidget(self.state_badge)

        layout.addSpacing(16)

        # Software reset — only enabled when E-STOPPED and Relay 1 is connected
        self.reset_btn = QPushButton("↺  RESET")
        self.reset_btn.setFixedSize(110, 44)
        self.reset_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.reset_btn.setEnabled(False)
        self.reset_btn.setToolTip(
            "Reset software state to IDLE.\n"
            "Only available after physical E-stop has been reset and Relay 1 is online."
        )
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a3a1a;
                color: #aaaaaa;
                border: 2px solid #2a5a2a;
                border-radius: 8px;
            }
            QPushButton:enabled {
                background-color: #1a5a1a;
                color: #ffffff;
                border: 2px solid #44aa44;
            }
            QPushButton:enabled:hover {
                background-color: #228822;
                border-color: #66cc66;
            }
            QPushButton:enabled:pressed {
                background-color: #115511;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #555555;
                border: 2px solid #333333;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_triggered.emit)
        layout.addWidget(self.reset_btn)

        layout.addSpacing(10)

        # Soft stop — cuts all relay channels via Modbus, does NOT cut physical power
        self.estop_btn = SoftStopButton()
        self.estop_btn.clicked.connect(self.estop_triggered.emit)
        layout.addWidget(self.estop_btn)

    def set_reset_enabled(self, enabled: bool):
        self.reset_btn.setEnabled(enabled)

    def update_connection(self, device: str, connected: bool, stale: bool = False):
        mapping = {
            "relay1":  self.conn_relay1,
            "relay2":  self.conn_relay2,
            "teensy1": self.conn_teensy1,
            "teensy2": self.conn_teensy2,
        }
        if device in mapping:
            mapping[device].set_connected(connected, stale)

    def set_state(self, state: str):
        self.state_badge.set_state(state)


# ── Placeholder tab ───────────────────────────────────────────────────────────
class PlaceholderTab(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"{name}\n(Coming soon)")
        lbl.setFont(QFont("Segoe UI", 16))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(lbl)


# ── Main window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    _relay_connection_result = pyqtSignal(int, bool)  # relay number, connected

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dig 'Em Aggies — TBM Operator Station")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(DARK_STYLE)

        self._system_state = State.ESTOPPED
        self._controls_unlocked = False
        self._relay2_alarm_active = False  # True when ch4 or ch5 on relay 2 is on
        self._alarm_timer = QTimer(self)
        self._alarm_timer.setSingleShot(True)
        self._alarm_timer.timeout.connect(self._on_alarm_timer_expired)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self.topbar = TopBar()
        self.topbar.estop_triggered.connect(self._handle_estop)
        self.topbar.reset_triggered.connect(self.software_reset)
        root.addWidget(self.topbar)

        self._mining_active = False

        # MQTT publisher
        self._mqtt = MQTTPublisher(self)
        self._mqtt.status_changed.connect(
            lambda msg: self.statusBar().showMessage(f"MQTT: {msg}")
        )

        self._relay1_connected = False
        self._relay2_connected = False

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        root.addWidget(self.tabs)

        # Add tabs
        self.tab_dashboard = DashboardTab()
        self.tab_dashboard.state_change_requested.connect(self._set_state)
        self.tab_dashboard.mining_toggled.connect(self._on_mining_toggled)
        self.tab_machine   = MachineStateTab()
        self.tab_power     = PowerTab()
        self.tab_controls  = ControlsTab()
        self.tab_controls.channel_toggled.connect(self._on_channel_toggled)
        self.tab_log       = LogTab()
        self.tab_io        = IOListTab()

        self.tabs.addTab(self.tab_dashboard, "Dashboard")
        self.tabs.addTab(self.tab_machine,   "Machine State")
        self.tabs.addTab(self.tab_power,     "Power")
        self.tabs.addTab(self.tab_controls,  "Controls")
        self.tabs.addTab(self.tab_log,       "Log")
        self.tabs.addTab(self.tab_io,        "IO List")

        # Lock controls tab behind password
        self.tabs.currentChanged.connect(self._on_tab_change)
        self._controls_tab_index = 3

        # Status bar
        self.statusBar().setStyleSheet("background-color: #3a0000; color: #ffffff; border-top: 1px solid #7a1515; font-size: 13px;")
        self.statusBar().showMessage("System initializing...")

        # Relay connection polling
        self._relay_connection_result.connect(self._on_relay_connection_result)
        self._conn_timer = QTimer()
        self._conn_timer.timeout.connect(self._poll_connections)
        self._conn_timer.start(2000)

        # UDP listener — receives Teensy broadcasts
        self._udp = UDPListener(self)
        self._udp.sensor_received.connect(self.dispatch_sensor)
        self._udp.power_received.connect(self.dispatch_power)
        self._udp.connection_changed.connect(self.topbar.update_connection)
        self._udp.start()

    def _on_tab_change(self, index):
        if index == self._controls_tab_index and not self._controls_unlocked:
            # Block the switch, show password dialog
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self._prev_tab_index if hasattr(self, '_prev_tab_index') else 0)
            self.tabs.blockSignals(False)

            dlg = PasswordDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                if dlg.password() == CONTROLS_PASSWORD:
                    self._controls_unlocked = True
                    self.tabs.setCurrentIndex(self._controls_tab_index)
                    self.statusBar().showMessage("Controls unlocked.")
                else:
                    QMessageBox.warning(self, "Access Denied", "Incorrect password.")
        else:
            self._prev_tab_index = index

    def _handle_estop(self):
        self._set_state(State.ESTOPPED)
        self.tab_controls.all_outputs_off()
        self.tab_log.log_estop()
        self.statusBar().showMessage("⚠ ALL OUTPUTS OFF — All relay channels zeroed via software. Physical power still live.")
        # TODO: send all-off command to relay 1 and relay 2 via Modbus

    def _set_state(self, state: str, buzzer: bool = False):
        # Guard invalid transitions from dashboard buttons
        if state == State.RUNNING and self._system_state != State.IDLE:
            return
        if state == State.IDLE and self._system_state not in (State.RUNNING, State.STARTING, State.ESTOPPED):
            return
        self._system_state = state
        self.topbar.set_state(state)
        self.tab_dashboard.set_system_state(state)
        self.tab_machine.set_system_state(state)
        self.tab_power.set_system_state(state)
        self.tab_controls.set_system_state(state)
        self.tab_log.log_state(state)
        self._apply_signal_lights(state, buzzer=buzzer)
        # Reset button only enabled when E-STOPPED and Relay 1 is back online
        self.topbar.set_reset_enabled(
            state == State.ESTOPPED and self._relay1_connected
        )

    def _set_relay1_connected(self, connected: bool):
        was_connected = self._relay1_connected
        self._relay1_connected = connected
        self.topbar.update_connection("relay1", connected)
        self.topbar.set_reset_enabled(
            self._system_state == State.ESTOPPED and connected
        )
        # Auto-reset to IDLE when relay 1 comes online from E-STOPPED
        if not was_connected and connected and self._system_state == State.ESTOPPED:
            self.software_reset()
        # Physical E-brake cuts Relay 1 power — detect as connection drop
        if was_connected and not connected:
            self._set_state(State.ESTOPPED, buzzer=True)
            self._set_alarm_light(True)
            self._alarm_timer.start(5000)
            self.tab_log.log_estop()

    def closeEvent(self, event):
        self._udp.stop()
        self._mqtt.shutdown()
        super().closeEvent(event)

    def dispatch_sensor(self, key: str, value: float):
        """Called by comms layer when a Teensy sensor value arrives."""
        self.tab_dashboard.update_sensor(key, value)
        self.tab_machine.update_sensor(key, value)
        self.tab_io.update_sensor(key, value)
        self._mqtt.update_sensor(key, value)

    def dispatch_power(self, key: str, voltage: float, current: float):
        """Called by comms layer when a power rail reading arrives."""
        self.tab_dashboard.update_power(key, voltage, current)
        self.tab_power.update_power(key, voltage, current)
        self._mqtt.update_power(key, voltage, current)

    def _on_channel_toggled(self, relay: int, ch: int, state: bool):
        from controls_tab import RELAY1_CHANNELS, RELAY2_CHANNELS
        channels = RELAY1_CHANNELS if relay == 1 else RELAY2_CHANNELS
        label = channels.get(ch, ("CH" + str(ch), "", False, False))[0]
        self.tab_log.log_relay(relay, ch, label, state)
        self.tab_io.update_relay(relay, ch, state)
        if relay == 1 and ch in (7, 8):
            self.tab_power.set_pump_state(state)
        if relay == 2 and ch in (4, 5):
            self._relay2_alarm_active = state
            self._set_alarm_light(state)
        import threading
        threading.Thread(target=self._modbus_write_coil,
                         args=(relay, ch, state), daemon=True).start()

    def _modbus_write_coil(self, relay: int, ch: int, state: bool):
        from pymodbus.client import ModbusTcpClient
        key  = f"relay{relay}"
        ip   = NETWORK[key]["ip"]
        port = NETWORK[key]["port"]
        try:
            c = ModbusTcpClient(ip, port=port, timeout=2)
            if c.connect():
                c.write_coil(ch - 1, state)
                c.close()
        except Exception:
            pass

    def _apply_signal_lights(self, state: str, buzzer: bool = False):
        # CH1=Green, CH2=Yellow, CH3=Red, CH4=Buzzer, CH5=GND (always on)
        lights = {
            State.RUNNING:  {1: True,  2: False, 3: False},
            State.IDLE:     {1: False, 2: True,  3: False},
            State.STARTING: {1: False, 2: True,  3: False},
            State.ESTOPPED: {1: False, 2: False, 3: True },
        }
        mapping = lights.get(state, {})
        mapping[4] = buzzer   # CH4 buzzer
        mapping[5] = True     # CH5 GND always on
        for ch, val in mapping.items():
            self.tab_controls.set_channel(2, ch, val)
        import threading
        threading.Thread(target=self._write_signal_lights,
                         args=(dict(mapping),), daemon=True).start()

    def _write_signal_lights(self, mapping: dict):
        from pymodbus.client import ModbusTcpClient
        ip   = NETWORK["relay2"]["ip"]
        port = NETWORK["relay2"]["port"]
        try:
            c = ModbusTcpClient(ip, port=port, timeout=2)
            if c.connect():
                for ch, val in mapping.items():
                    c.write_coil(ch - 1, val)
                c.close()
        except Exception:
            pass

    def _set_alarm_light(self, on: bool):
        self.tab_dashboard.signal_panel.set_light("alarm", on)

    def _on_alarm_timer_expired(self):
        if not self._relay2_alarm_active:
            self._set_alarm_light(False)
        # Turn buzzer off after 5s
        self._apply_signal_lights(self._system_state, buzzer=False)

    def _on_mining_toggled(self, active: bool):
        self._mining_active = active
        self._mqtt.set_mining(active)
        self.tab_log.log_mining(active)
        self.statusBar().showMessage(
            f"Mining {'STARTED' if active else 'STOPPED'} — MQTT telemetry {'publishing' if active else 'paused'}."
        )

    def _poll_connections(self):
        import threading
        threading.Thread(target=self._poll_relay, args=(1,), daemon=True).start()
        threading.Thread(target=self._poll_relay, args=(2,), daemon=True).start()

    def _poll_relay(self, relay: int):
        from pymodbus.client import ModbusTcpClient
        key  = f"relay{relay}"
        ip   = NETWORK[key]["ip"]
        port = NETWORK[key]["port"]
        try:
            c  = ModbusTcpClient(ip, port=port, timeout=1)
            ok = c.connect()
            c.close()
        except Exception:
            ok = False
        self._relay_connection_result.emit(relay, ok)

    def _on_relay_connection_result(self, relay: int, connected: bool):
        if relay == 1:
            self._set_relay1_connected(connected)
        else:
            if connected != self._relay2_connected:
                self._relay2_connected = connected
                self.topbar.update_connection("relay2", connected)

    def software_reset(self):
        """Software-only reset — clears E-STOPPED state back to IDLE.
        Requires physical E-stop to have been reset first (Relay 1 must be online)."""
        if self._system_state == State.ESTOPPED and self._relay1_connected:
            self._set_state(State.IDLE)
            self.tab_dashboard.warnings.clear_all()
            self.tab_dashboard.warnings.show_all_clear()
            self.tab_log.log_reset()
            self.statusBar().showMessage("Software reset — system IDLE. Physical E-stop confirmed clear.")


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DiGEM TBM Operator Station")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
