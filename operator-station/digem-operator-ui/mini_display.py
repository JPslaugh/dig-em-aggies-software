"""
Mini Display — Dig 'Em Aggies
Compact operator display for 1024x600 Pi screen.
"""

import sys
import os
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import time
import threading
import traceback

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGridLayout, QFrame, QSizePolicy, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont

from config import NETWORK, STALE_TIMEOUT, IO_THRESHOLDS, State
from udp_listener import UDPListener

# ── Colours ───────────────────────────────────────────────────────────────────
BG      = "#1a0000"
CARD_BG = "#2a0000"
BORDER  = "#7a1515"
TEXT    = "#ffffff"
DIM     = "#806060"
GREEN   = "#4caf50"
YELLOW  = "#c8820a"
RED     = "#cc2222"
BLUE    = "#4488cc"

STYLE = f"""
QMainWindow, QWidget {{ background-color: {BG}; color: {TEXT}; font-family: 'Segoe UI', sans-serif; }}
QLabel {{ color: {TEXT}; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; background-color: {BG}; }}
QTabBar::tab {{
    background-color: #500000; color: {TEXT}; padding: 8px 24px;
    border: 1px solid {BORDER}; border-bottom: none; font-size: 12px; font-weight: bold;
}}
QTabBar::tab:selected {{ background-color: {BG}; border-bottom: 2px solid {RED}; }}
QTabBar::tab:hover:!selected {{ background-color: #6a0000; }}
"""

def _font(size, bold=False):
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    return f


# ── Sensor card ───────────────────────────────────────────────────────────────
class SensorCard(QFrame):
    def __init__(self, key, label, unit):
        super().__init__()
        self._key = key
        self._t   = IO_THRESHOLDS.get(key, {})
        self.setFixedHeight(54)
        self.setStyleSheet(f"background:{CARD_BG}; border:1px solid {BORDER}; border-radius:4px;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 8, 2)
        self._lbl = QLabel(label)
        self._lbl.setFont(_font(9))
        self._lbl.setStyleSheet(f"color:{DIM};")
        self._lbl.setFixedWidth(52)
        self._val = QLabel("—")
        self._val.setFont(_font(14, bold=True))
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._unit = QLabel(unit)
        self._unit.setFont(_font(8))
        self._unit.setStyleSheet(f"color:{DIM};")
        self._unit.setFixedWidth(28)
        self._status = QLabel("")
        self._status.setFont(_font(7, bold=True))
        self._status.setFixedWidth(44)
        self._status.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._lbl)
        lay.addStretch()
        lay.addWidget(self._val)
        lay.addWidget(self._unit)
        lay.addWidget(self._status)

    def update_value(self, value):
        self._val.setText(f"{value:.1f}")
        t = self._t
        color, status = GREEN, ""
        if t:
            if value <= t.get("low_alarm", -999) or value >= t.get("high_alarm", 999):
                color, status = RED, "ALARM"
            elif value <= t.get("low_warn", -999) or value >= t.get("high_warn", 999):
                color, status = YELLOW, "WARN"
        self._val.setStyleSheet(f"color:{color};")
        self._status.setText(status)
        self._status.setStyleSheet(f"color:{color};")
        self.setStyleSheet(f"background:{CARD_BG}; border:1px solid {color if status else BORDER}; border-radius:4px;")


# ── Connection dot ────────────────────────────────────────────────────────────
class ConnDot(QLabel):
    def __init__(self, label):
        super().__init__(f"● {label}")
        self.setFont(_font(8))
        self.set_connected(False)

    def set_connected(self, ok, stale=False):
        color = YELLOW if stale else (GREEN if ok else RED)
        self.setStyleSheet(f"color:{color};")


# ── State badge ───────────────────────────────────────────────────────────────
class StateBadge(QLabel):
    COLORS = {State.ESTOPPED: RED, State.IDLE: YELLOW, State.STARTING: YELLOW, State.RUNNING: GREEN}

    def __init__(self):
        super().__init__(State.ESTOPPED)
        self.setFont(_font(12, bold=True))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(34)
        self._apply(State.ESTOPPED)

    def set_state(self, state):
        self.setText(state)
        self._apply(state)

    def _apply(self, state):
        c = self.COLORS.get(state, DIM)
        self.setStyleSheet(f"color:{c}; border:2px solid {c}; border-radius:4px; padding:2px 8px;")


# ── Warning list ──────────────────────────────────────────────────────────────
class WarningList(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{CARD_BG}; border:1px solid {BORDER}; border-radius:4px;")
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(6, 4, 6, 4)
        self._lay.setSpacing(2)
        self._entries = {}
        self._none = QLabel("No active warnings")
        self._none.setFont(_font(8))
        self._none.setStyleSheet(f"color:{DIM};")
        self._none.setAlignment(Qt.AlignCenter)
        self._lay.addWidget(self._none)

    def set_warning(self, key, msg, alarm):
        if key not in self._entries:
            lbl = QLabel()
            lbl.setFont(_font(8))
            lbl.setWordWrap(True)
            self._lay.addWidget(lbl)
            self._entries[key] = lbl
        color = RED if alarm else YELLOW
        self._entries[key].setText(f"{'⬛' if alarm else '⚠'} {msg}")
        self._entries[key].setStyleSheet(f"color:{color};")
        self._none.hide()

    def clear_warning(self, key):
        if key in self._entries:
            self._entries[key].hide()
            del self._entries[key]
        if not self._entries:
            self._none.show()


# ── Relay channel indicator ───────────────────────────────────────────────────
class ChannelIndicator(QFrame):
    def __init__(self, ch, label):
        super().__init__()
        self.setFixedHeight(44)
        self._off_style = f"background:{CARD_BG}; border:1px solid {BORDER}; border-radius:4px;"
        self._on_style  = f"background:#1a4a1a; border:1px solid {GREEN}; border-radius:4px;"
        self.setStyleSheet(self._off_style)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 6, 2)
        ch_lbl = QLabel(f"CH{ch:02d}")
        ch_lbl.setFont(_font(8, bold=True))
        ch_lbl.setStyleSheet(f"color:{DIM};")
        ch_lbl.setFixedWidth(32)
        self._name = QLabel(label)
        self._name.setFont(_font(8))
        self._state = QLabel("OFF")
        self._state.setFont(_font(9, bold=True))
        self._state.setStyleSheet(f"color:{DIM};")
        self._state.setAlignment(Qt.AlignRight)
        lay.addWidget(ch_lbl)
        lay.addWidget(self._name)
        lay.addStretch()
        lay.addWidget(self._state)

    def set_state(self, on):
        if on:
            self.setStyleSheet(self._on_style)
            self._state.setText("ON")
            self._state.setStyleSheet(f"color:{GREEN}; font-weight:bold;")
        else:
            self.setStyleSheet(self._off_style)
            self._state.setText("OFF")
            self._state.setStyleSheet(f"color:{DIM};")


# ── Relay tab ─────────────────────────────────────────────────────────────────
class RelayTab(QWidget):
    _states_signal = pyqtSignal(int, list)  # relay, states[16]

    def __init__(self):
        super().__init__()
        from controls_tab import RELAY1_CHANNELS, RELAY2_CHANNELS

        self._states_signal.connect(self._apply_states)
        self._indicators = {}  # (relay, ch) -> ChannelIndicator

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)

        for relay, channels, label in (
            (1, RELAY1_CHANNELS, "Relay 1 — Harmful Devices"),
            (2, RELAY2_CHANNELS, "Relay 2 — Non-Harmful Devices"),
        ):
            col = QVBoxLayout()
            col.setSpacing(4)
            hdr = QLabel(label)
            hdr.setFont(_font(9, bold=True))
            hdr.setStyleSheet(f"color:{DIM};")
            col.addWidget(hdr)
            grid = QGridLayout()
            grid.setSpacing(3)
            for idx, (ch, (lbl, *_)) in enumerate(channels.items()):
                ind = ChannelIndicator(ch, lbl)
                self._indicators[(relay, ch)] = ind
                grid.addWidget(ind, idx // 2, idx % 2)
            col.addLayout(grid)
            col.addStretch()
            lay.addLayout(col)

    @pyqtSlot(int, list)
    def _apply_states(self, relay, states):
        for i, on in enumerate(states):
            key = (relay, i + 1)
            if key in self._indicators:
                self._indicators[key].set_state(on)

    def update_relay(self, relay, states):
        self._states_signal.emit(relay, states)


# ── Main window ───────────────────────────────────────────────────────────────
class MiniDisplay(QMainWindow):
    _relay_result = pyqtSignal(int, bool, list)  # relay, connected, coil states

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dig 'Em Aggies — Mini Display")
        self.setStyleSheet(STYLE)
        self.showFullScreen()

        self._system_state     = State.ESTOPPED
        self._relay1_connected = False
        self._relay2_connected = False

        self._build_ui()

        self._udp = UDPListener(self)
        self._udp.sensor_received.connect(self._on_sensor)
        self._udp.power_received.connect(self._on_power)
        self._udp.connection_changed.connect(self._on_connection)
        self._udp.start()

        self._relay_result.connect(self._on_relay_result)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_relays)
        self._poll_timer.start(2000)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(8, 6, 8, 6)
        main.setSpacing(4)

        # Top bar
        top = QHBoxLayout()
        title = QLabel("DIG 'EM AGGIES")
        title.setFont(_font(11, bold=True))
        title.setStyleSheet(f"color:{BLUE};")
        self._state_badge = StateBadge()
        self._conn_r1 = ConnDot("Relay 1")
        self._conn_r2 = ConnDot("Relay 2")
        self._conn_t1 = ConnDot("Teensy 1")
        self._conn_t2 = ConnDot("Teensy 2")
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self._state_badge)
        top.addSpacing(16)
        for d in [self._conn_r1, self._conn_r2, self._conn_t1, self._conn_t2]:
            top.addWidget(d)
        main.addLayout(top)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background:{BORDER}; max-height:1px;")
        main.addWidget(div)

        # Tabs
        self._tabs = QTabWidget()

        # ── Tab 1: Overview ──
        overview = QWidget()
        body = QHBoxLayout(overview)
        body.setContentsMargins(0, 6, 0, 0)
        body.setSpacing(8)

        sensor_frame = QWidget()
        grid = QGridLayout(sensor_frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        sensors = [
            ("RPM",        "RPM",    "RPM"),
            ("Flow",       "Flow",   "L/m"),
            ("Depth",      "Depth",  "m"),
            ("Roll",       "Roll",   "°"),
            ("Pitch",      "Pitch",  "°"),
            ("Yaw",        "Yaw",    "°"),
            ("Encl_Temp1", "Temp 1", "°C"),
            ("Encl_Temp2", "Temp 2", "°C"),
        ]
        self._cards = {}
        for i, (key, label, unit) in enumerate(sensors):
            card = SensorCard(key, label, unit)
            self._cards[key] = card
            grid.addWidget(card, i // 2, i % 2)

        power_frame = QWidget()
        power_lay = QGridLayout(power_frame)
        power_lay.setContentsMargins(0, 0, 0, 0)
        power_lay.setSpacing(4)
        self._power_labels = {}
        for i, (key, lbl) in enumerate([("relay1","R1"),("relay2","R2"),("24v","24V"),("12v","12V")]):
            f = QFrame()
            f.setFixedHeight(34)
            f.setStyleSheet(f"background:{CARD_BG}; border:1px solid {BORDER}; border-radius:4px;")
            fl = QHBoxLayout(f)
            fl.setContentsMargins(6, 2, 6, 2)
            n = QLabel(lbl)
            n.setFont(_font(8))
            n.setStyleSheet(f"color:{DIM};")
            v = QLabel("—")
            v.setFont(_font(9, bold=True))
            v.setAlignment(Qt.AlignRight)
            fl.addWidget(n)
            fl.addStretch()
            fl.addWidget(v)
            self._power_labels[key] = v
            power_lay.addWidget(f, i // 2, i % 2)

        left = QVBoxLayout()
        left.setSpacing(4)
        left.addWidget(sensor_frame)
        left.addWidget(power_frame)

        self._warnings = WarningList()
        self._warnings.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        body.addLayout(left, stretch=3)
        body.addWidget(self._warnings, stretch=2)
        self._tabs.addTab(overview, "Overview")

        # ── Tab 2: Relay Channels ──
        self._relay_tab = RelayTab()
        self._tabs.addTab(self._relay_tab, "Relay Channels")

        main.addWidget(self._tabs, stretch=1)

    def _on_sensor(self, key, value):
        if key in self._cards:
            self._cards[key].update_value(value)
        t = IO_THRESHOLDS.get(key, {})
        if t:
            if value <= t.get("low_alarm", -999) or value >= t.get("high_alarm", 999):
                self._warnings.set_warning(f"{key}_alarm", f"{key}: {value:.1f} — ALARM", alarm=True)
            elif value <= t.get("low_warn", -999) or value >= t.get("high_warn", 999):
                self._warnings.set_warning(f"{key}_warn", f"{key}: {value:.1f} — WARN", alarm=False)
            else:
                self._warnings.clear_warning(f"{key}_alarm")
                self._warnings.clear_warning(f"{key}_warn")

    def _on_power(self, key, voltage, current):
        if key in self._power_labels:
            self._power_labels[key].setText(f"{voltage:.1f}V  {current:.1f}A")

    def _on_connection(self, device, connected, stale):
        mapping = {"teensy1": self._conn_t1, "teensy2": self._conn_t2}
        if device in mapping:
            mapping[device].set_connected(connected, stale)

    def _poll_relays(self):
        for relay in (1, 2):
            threading.Thread(target=self._poll_relay, args=(relay,), daemon=True).start()

    def _poll_relay(self, relay):
        from pymodbus.client import ModbusTcpClient
        key  = f"relay{relay}"
        ip   = NETWORK[key]["ip"]
        port = NETWORK[key]["port"]
        states = [False] * 16
        try:
            c = ModbusTcpClient(ip, port=port, timeout=1)
            ok = c.connect()
            if ok:
                result = c.read_coils(0, count=16)
                if result and not result.isError():
                    states = list(result.bits[:16])
            c.close()
        except Exception:
            ok = False
        self._relay_result.emit(relay, ok, states)

    @pyqtSlot(int, bool, list)
    def _on_relay_result(self, relay, connected, states):
        if relay == 1:
            was = self._relay1_connected
            self._relay1_connected = connected
            self._conn_r1.set_connected(connected)
            if not was and connected and self._system_state == State.ESTOPPED:
                self._set_state(State.IDLE)
            if was and not connected:
                self._set_state(State.ESTOPPED)
                self._warnings.set_warning("estop", "E-BRAKE PRESSED — Relay 1 offline", alarm=True)
        else:
            self._relay2_connected = connected
            self._conn_r2.set_connected(connected)
        if connected:
            self._relay_tab.update_relay(relay, states)

    def _set_state(self, state):
        self._system_state = state
        self._state_badge.set_state(state)
        if state != State.ESTOPPED:
            self._warnings.clear_warning("estop")


def main():
    app = QApplication(sys.argv)
    w = MiniDisplay()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    sys.excepthook = lambda t, v, tb: traceback.print_exception(t, v, tb)
    main()
