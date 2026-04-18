from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QSizePolicy, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
import time

from config import IO_THRESHOLDS, STALE_TIMEOUT, State

#Helpers

def threshold_color(key, value):
    t = IO_THRESHOLDS.get(key)
    if t is None:
        return "#e8d5d5"
    if value <= t["low_alarm"] or value >= t["high_alarm"]:
        return "#cc2222"
    if value <= t["low_warn"] or value >= t["high_warn"]:
        return "#c8820a"
    return "#4caf50"

def threshold_label(key, value):
    t = IO_THRESHOLDS.get(key)
    if t is None:
        return ""
    if value <= t["low_alarm"]:  return "LOW ALARM"
    if value >= t["high_alarm"]: return "HIGH ALARM"
    if value <= t["low_warn"]:   return "LOW WARN"
    if value >= t["high_warn"]:  return "HIGH WARN"
    return "NORMAL"

def bar_fraction(key, value):
    t = IO_THRESHOLDS.get(key)
    if t is None:
        return 0.5
    lo, hi = t["low_alarm"], t["high_alarm"]
    if hi == lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))

CARD_BG        = "#500000"   # Texas A&M maroon
CARD_BORDER    = "#7a1515"   # slightly lighter
SECTION_BG     = "#1a0000"
LABEL_COLOR    = "#ffffff"
NODATA_COLOR   = "#aaaaaa"

# Signal light auto-mapping per system state:
# green=running, yellow=idle/starting, red=estopped, alarm=any active alarm
STATE_LIGHTS = {
    State.ESTOPPED: {"green": False, "yellow": False, "red": True,  "alarm": False},
    State.IDLE:     {"green": False, "yellow": True,  "red": False, "alarm": False},
    State.STARTING: {"green": False, "yellow": True,  "red": False, "alarm": False},
    State.RUNNING:  {"green": True,  "yellow": False, "red": False, "alarm": False},
}


#Mini bar widget
class MiniBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._fraction = 0.0
        self._color = "#4caf50"

    def set_value(self, fraction, color):
        self._fraction = fraction
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor("#3a1010"))
        fill_w = int(w * self._fraction)
        if fill_w > 0:
            p.fillRect(0, 0, fill_w, h, QColor(self._color))
        p.end()


# Single sensor value card
class SensorCard(QFrame):
    def __init__(self, key, label, parent=None):
        super().__init__(parent)
        self.key = key
        self._last_update = None
        self._startup_time = time.time()  # FIX #2: track startup for never-connected stale

        self.setFrameShape(QFrame.StyledPanel)
        self._set_border(CARD_BORDER)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.name_lbl = QLabel(label)
        self.name_lbl.setFont(QFont("Segoe UI", 13))
        self.name_lbl.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        layout.addWidget(self.name_lbl)

        self.val_lbl = QLabel("—")
        self.val_lbl.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.val_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        layout.addWidget(self.val_lbl)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.bar = MiniBar()
        bottom.addWidget(self.bar, stretch=1)

        right = QVBoxLayout()
        right.setSpacing(1)
        self.status_lbl = QLabel("NO DATA")
        self.status_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.status_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        right.addWidget(self.status_lbl)

        # FIX #7: last received timestamp
        self.time_lbl = QLabel("")
        self.time_lbl.setFont(QFont("Segoe UI", 9))
        self.time_lbl.setStyleSheet("color: #888888; border: none;")
        right.addWidget(self.time_lbl)
        bottom.addLayout(right)
        layout.addLayout(bottom)

    def _set_border(self, color):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {color};
                border-radius: 6px;
            }}
        """)

    def update_value(self, value):
        self._last_update = time.time()
        t = IO_THRESHOLDS.get(self.key, {})
        unit = t.get("unit", "")
        color = threshold_color(self.key, value)
        label = threshold_label(self.key, value)
        frac  = bar_fraction(self.key, value)

        self.val_lbl.setText(f"{value:.1f} {unit}")
        self.val_lbl.setStyleSheet(f"color: {color}; border: none;")
        self.bar.set_value(frac, color)
        self.status_lbl.setText(label)
        self.status_lbl.setStyleSheet(f"color: {color}; border: none;")
        self.time_lbl.setText(time.strftime("%H:%M:%S"))
        self._set_border(color + "99")

    def mark_stale(self):
        self.val_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        self.status_lbl.setText("STALE")
        self.status_lbl.setStyleSheet("color: #c8820a; border: none;")
        self.bar.set_value(0, NODATA_COLOR)
        self._set_border("#c8820a")

    def check_stale(self):
        if self._last_update and time.time() - self._last_update > STALE_TIMEOUT:
            self.mark_stale()


#Power rail card
class PowerCard(QFrame):
    def __init__(self, label, v_key, a_key, parent=None):
        super().__init__(parent)
        self.v_key = v_key
        self.a_key = a_key

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 6px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title = QLabel(label)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.v_lbl = QLabel("—  V")
        self.v_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.v_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        row.addWidget(self.v_lbl)

        sep = QLabel("|")
        sep.setFont(QFont("Segoe UI", 22))
        sep.setStyleSheet(f"color: {CARD_BORDER}; border: none;")
        row.addWidget(sep)

        self.a_lbl = QLabel("—  A")
        self.a_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.a_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        row.addWidget(self.a_lbl)
        row.addStretch()
        layout.addLayout(row)

        self.w_lbl = QLabel("—  W")
        self.w_lbl.setFont(QFont("Segoe UI", 13))
        self.w_lbl.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        layout.addWidget(self.w_lbl)

    def update_values(self, voltage, current):
        v_color = threshold_color(self.v_key, voltage)
        a_color = threshold_color(self.a_key, current)
        self.v_lbl.setText(f"{voltage:.2f}  V")
        self.v_lbl.setStyleSheet(f"color: {v_color}; border: none;")
        self.a_lbl.setText(f"{current:.2f}  A")
        self.a_lbl.setStyleSheet(f"color: {a_color}; border: none;")
        self.w_lbl.setText(f"{voltage * current:.1f}  W")
        self.w_lbl.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")


#Signal light panel
class SignalLightPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(24)

        title = QLabel("Signal Tower")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        layout.addWidget(title)

        self.lights = {}
        defs = [
            ("green",  "●", "#4caf50", "Green"),
            ("yellow", "●", "#c8820a", "Yellow"),
            ("red",    "●", "#cc2222", "Red"),
            ("alarm",  "▲", "#e05020", "Alarm"),
        ]
        for key, sym, color, lbl_text in defs:
            col = QVBoxLayout()
            col.setSpacing(2)
            dot = QLabel(sym)
            dot.setFont(QFont("Segoe UI", 32))
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet("color: #2a0d0d; border: none;")
            lbl = QLabel(lbl_text)
            lbl.setFont(QFont("Segoe UI", 12))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
            col.addWidget(dot)
            col.addWidget(lbl)
            layout.addLayout(col)
            self.lights[key] = (dot, color)

        layout.addStretch()

    def set_light(self, key, on: bool):
        if key in self.lights:
            dot, color = self.lights[key]
            dot.setStyleSheet(f"color: {'#2a0d0d' if not on else color}; border: none;")

    def apply_state(self, state: str, has_alarm: bool = False):
        """FIX #4: auto-set lights based on system state."""
        mapping = STATE_LIGHTS.get(state, STATE_LIGHTS[State.ESTOPPED]).copy()
        if has_alarm:
            mapping["alarm"] = True
        for key, on in mapping.items():
            self.set_light(key, on)


# MQTT status card
class MQTTStatusCard(QFrame):
    mining_toggled = pyqtSignal(bool)  # FIX #5: mining flag toggle

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mining = False
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 6px;
            }}
        """)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        title = QLabel("MQTT Telemetry")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        top_row.addWidget(title)
        top_row.addStretch()

        # FIX #5: mining toggle button
        self.mining_btn = QPushButton("⛏  MINING: OFF")
        self.mining_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.mining_btn.setFixedHeight(32)
        self.mining_btn.setCheckable(True)
        self._update_mining_btn(False)
        self.mining_btn.clicked.connect(self._on_mining_toggled)
        top_row.addWidget(self.mining_btn)
        layout.addLayout(top_row)

        row = QHBoxLayout()
        self.dot = QLabel("●")
        self.dot.setFont(QFont("Segoe UI", 24))
        self.dot.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        row.addWidget(self.dot)
        self.status_lbl = QLabel("Not connected")
        self.status_lbl.setFont(QFont("Segoe UI", 16))
        self.status_lbl.setStyleSheet(f"color: {NODATA_COLOR}; border: none;")
        row.addWidget(self.status_lbl)
        row.addStretch()
        self.last_pub = QLabel("Last publish: —")
        self.last_pub.setFont(QFont("Segoe UI", 13))
        self.last_pub.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        row.addWidget(self.last_pub)
        layout.addLayout(row)

    def _update_mining_btn(self, active: bool):
        if active:
            self.mining_btn.setText("⛏  MINING: ON")
            self.mining_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5a1a;
                    color: #ffffff;
                    border: 2px solid #44aa44;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #228822; }
            """)
        else:
            self.mining_btn.setText("⛏  MINING: OFF")
            self.mining_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a1a1a;
                    color: #aaaaaa;
                    border: 2px solid #5a3030;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover { background-color: #3a2020; }
            """)

    def _on_mining_toggled(self):
        self._mining = not self._mining
        self._update_mining_btn(self._mining)
        self.mining_toggled.emit(self._mining)

    def reset_mining(self):
        self._mining = False
        self.mining_btn.setChecked(False)
        self._update_mining_btn(False)

    def set_connected(self, connected: bool):
        color = "#4caf50" if connected else "#cc2222"
        text  = "Connected"  if connected else "Disconnected"
        self.dot.setStyleSheet(f"color: {color}; border: none;")
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color}; border: none;")

    def set_last_publish(self, ts: str):
        self.last_pub.setText(f"Last publish: {ts}")

    @property
    def mining(self):
        return self._mining


#Warnings panel
class WarningsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._any_connected = False   # FIX #1: track connection state
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        title = QLabel("Active Warnings & Alarms")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll)

        self._entries = {}
        # FIX #1: show awaiting instead of all clear until connected
        self._show_awaiting()

    def _show_awaiting(self):
        if "__status__" not in self._entries:
            lbl = QLabel("◌   Awaiting connection...")
            lbl.setFont(QFont("Segoe UI", 13))
            lbl.setStyleSheet("color: #aaaaaa; border: none;")
            self._list_layout.insertWidget(0, lbl)
            self._entries["__status__"] = lbl

    def notify_connected(self):
        """Call when at least one device connects."""
        if not self._any_connected:
            self._any_connected = True
            self.clear_warning("__status__")
            self.show_all_clear()

    def set_warning(self, key: str, message: str, is_alarm: bool = False):
        color  = "#cc2222" if is_alarm else "#c8820a"
        prefix = "⬛ ALARM" if is_alarm else "⚠  WARN"
        text   = f"{prefix}  —  {message}"
        if key in self._entries:
            self._entries[key].setText(text)
            self._entries[key].setStyleSheet(f"color: {color}; border: none;")
        else:
            self.clear_warning("__ok__")
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 13))
            lbl.setStyleSheet(f"color: {color}; border: none;")
            self._list_layout.insertWidget(self._list_layout.count() - 1, lbl)
            self._entries[key] = lbl

    def clear_warning(self, key: str):
        if key in self._entries:
            self._entries[key].deleteLater()
            del self._entries[key]
        # Only show all clear if connected and no real warnings remain
        real = [k for k in self._entries if k not in ("__ok__", "__status__")]
        if not real and self._any_connected:
            self.show_all_clear()

    def clear_all(self):
        for key in list(self._entries.keys()):
            if key in self._entries:
                self._entries[key].deleteLater()
                del self._entries[key]

    def show_all_clear(self):
        if "__ok__" not in self._entries:
            lbl = QLabel("✓   All systems nominal")
            lbl.setFont(QFont("Segoe UI", 13))
            lbl.setStyleSheet("color: #4caf50; border: none;")
            self._list_layout.insertWidget(0, lbl)
            self._entries["__ok__"] = lbl

    def has_alarms(self):
        return any(k.endswith("_alarm") for k in self._entries)


def section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
    lbl.setStyleSheet(f"color: {LABEL_COLOR};")
    return lbl


class DashboardTab(QWidget):
    warning_raised  = pyqtSignal(str, str, bool)
    warning_cleared = pyqtSignal(str)
    state_change_requested = pyqtSignal(str)  # FIX #3: state transitions
    mining_toggled  = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._system_state = State.ESTOPPED
        self._build_ui()

        self._stale_timer = QTimer()
        self._stale_timer.timeout.connect(self._check_stale)
        self._stale_timer.start(2000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # State card — includes FIX #3 transition buttons
        state_card = QFrame()
        state_card.setFrameShape(QFrame.StyledPanel)
        state_card.setFixedWidth(240)
        state_card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 6px;
            }}
        """)
        sc_layout = QVBoxLayout(state_card)
        sc_layout.setContentsMargins(16, 14, 16, 14)
        sc_layout.setSpacing(8)

        sc_title = QLabel("System State")
        sc_title.setFont(QFont("Segoe UI", 14))
        sc_title.setStyleSheet(f"color: {LABEL_COLOR}; border: none;")
        sc_layout.addWidget(sc_title)

        self.state_lbl = QLabel(State.ESTOPPED)
        self.state_lbl.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.state_lbl.setAlignment(Qt.AlignCenter)
        self.state_lbl.setWordWrap(True)
        self.state_lbl.setStyleSheet("color: #cc2222; border: none;")
        sc_layout.addWidget(self.state_lbl)

        sc_layout.addStretch()

        # FIX #3: START button (IDLE → RUNNING)
        self.start_btn = QPushButton("▶  START")
        self.start_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.start_btn.setFixedHeight(36)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #1a5a1a;
                color: #ffffff;
                border: 2px solid #44aa44;
                border-radius: 4px;
            }
            QPushButton:enabled:hover { background-color: #228822; }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #555555;
                border: 2px solid #333333;
                border-radius: 4px;
            }
        """)
        self.start_btn.clicked.connect(lambda: self.state_change_requested.emit(State.RUNNING))
        sc_layout.addWidget(self.start_btn)

        # STOP button (RUNNING → IDLE)
        self.stop_btn = QPushButton("⏹  STOP")
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #5a3a00;
                color: #ffffff;
                border: 2px solid #c8820a;
                border-radius: 4px;
            }
            QPushButton:enabled:hover { background-color: #7a5000; }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #555555;
                border: 2px solid #333333;
                border-radius: 4px;
            }
        """)
        self.stop_btn.clicked.connect(lambda: self.state_change_requested.emit(State.IDLE))
        sc_layout.addWidget(self.stop_btn)

        row1.addWidget(state_card)

        self.warnings = WarningsPanel()
        row1.addWidget(self.warnings, stretch=1)
        root.addLayout(row1, stretch=3)

        root.addWidget(section_label("Machine Sensors"))

        self.sensor_cards = {}

        # Row A: RPM, Flow, Enclosure Temp 1, Enclosure Temp 2
        sens_row_a = QHBoxLayout()
        sens_row_a.setSpacing(8)
        for key, label in [
            ("RPM",        "Cutterhead RPM"),
            ("Flow",       "Flow Rate"),
            ("Encl_Temp1", "Enclosure Temp #1"),
            ("Encl_Temp2", "Enclosure Temp #2"),
        ]:
            card = SensorCard(key, label)
            self.sensor_cards[key] = card
            sens_row_a.addWidget(card)
        root.addLayout(sens_row_a, stretch=2)

        # Row B: Depth, Roll, Pitch, Yaw
        sens_row_b = QHBoxLayout()
        sens_row_b.setSpacing(8)
        for key, label in [
            ("Depth", "Depth"),
            ("Roll",  "Roll"),
            ("Pitch", "Pitch"),
            ("Yaw",   "Yaw / Heading"),
        ]:
            card = SensorCard(key, label)
            self.sensor_cards[key] = card
            sens_row_b.addWidget(card)
        root.addLayout(sens_row_b, stretch=2)

        root.addWidget(section_label("Power Rails"))

        self.power_cards = {}
        pwr_row = QHBoxLayout()
        pwr_row.setSpacing(8)
        for key, label, v_key, a_key in [
            ("relay1", "Relay 1",    "Relay1_V",  "Relay1_A"),
            ("relay2", "Relay 2",    "Relay2_V",  "Relay2_A"),
            ("24v",    "24V Supply", "Rail24V_V",  "Rail24V_A"),
            ("12v",    "12V Supply", "Rail12V_V",  "Rail12V_A"),
        ]:
            card = PowerCard(label, v_key, a_key)
            self.power_cards[key] = card
            pwr_row.addWidget(card)
        root.addLayout(pwr_row, stretch=2)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        self.signal_panel = SignalLightPanel()
        bottom_row.addWidget(self.signal_panel, stretch=2)
        self.mqtt_card = MQTTStatusCard()
        self.mqtt_card.mining_toggled.connect(self.mining_toggled.emit)
        bottom_row.addWidget(self.mqtt_card, stretch=1)
        root.addLayout(bottom_row, stretch=1)

        # Apply initial state to signal lights
        self.signal_panel.apply_state(State.ESTOPPED)


    def update_sensor(self, key: str, value: float):
        if key in self.sensor_cards:
            self.sensor_cards[key].update_value(value)
            lbl = threshold_label(key, value)
            if lbl in ("LOW ALARM", "HIGH ALARM"):
                self.warnings.clear_warning(f"{key}_warn")
                self.warnings.set_warning(f"{key}_alarm", f"{key}: {value:.1f} — {lbl}", is_alarm=True)
                self.warning_raised.emit(f"{key}_alarm", f"{key}: {lbl}", True)
            elif lbl in ("LOW WARN", "HIGH WARN"):
                self.warnings.clear_warning(f"{key}_alarm")
                self.warnings.set_warning(f"{key}_warn", f"{key}: {value:.1f} — {lbl}", is_alarm=False)
                self.warning_raised.emit(f"{key}_warn", f"{key}: {lbl}", False)
            else:
                self.warnings.clear_warning(f"{key}_alarm")
                self.warnings.clear_warning(f"{key}_warn")
                self.warning_cleared.emit(key)
                # Clear alarm light if no more alarms
                if not self.warnings.has_alarms():
                    self.signal_panel.set_light("alarm", False)

    def update_power(self, key: str, voltage: float, current: float):
        if key in self.power_cards:
            self.power_cards[key].update_values(voltage, current)

    def update_signal_light(self, key: str, on: bool):
        self.signal_panel.set_light(key, on)

    def notify_device_connected(self):
        """Call when any device first connects."""
        self.warnings.notify_connected()

    def set_mqtt_connected(self, connected: bool):
        self.mqtt_card.set_connected(connected)

    def set_mqtt_last_publish(self, ts: str):
        self.mqtt_card.set_last_publish(ts)

    def set_system_state(self, state: str):
        self._system_state = state
        colors = {
            State.ESTOPPED: "#cc2222",
            State.IDLE:     "#c8820a",
            State.STARTING: "#4a7fc4",
            State.RUNNING:  "#4caf50",
        }
        color = colors.get(state, "#e8d5d5")
        self.state_lbl.setText(state)
        self.state_lbl.setStyleSheet(f"color: {color}; border: none;")

        # FIX #3: enable/disable start/stop based on state
        self.start_btn.setEnabled(state == State.IDLE)
        self.stop_btn.setEnabled(state == State.RUNNING)

        # FIX #4: auto-update signal lights
        self.signal_panel.apply_state(state, has_alarm=self.warnings.has_alarms())

        # Reset mining flag on E-stop
        if state == State.ESTOPPED:
            self.mqtt_card.reset_mining()

    def _check_stale(self):
        for card in self.sensor_cards.values():
            card.check_stale()
