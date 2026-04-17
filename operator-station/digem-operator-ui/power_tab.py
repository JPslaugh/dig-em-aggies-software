"""
Power Tab
---------
4 DC rail cards (Relay 1, Relay 2, 24V Supply, 12V Supply):
  - Live V / A / W with threshold colouring
  - Scrolling 60s history graph per rail
  - Utilization bar vs rated max

120VAC pump channel indicator (Relay_1 CH7/8) — on/off state only, no metering.
"""

import time
from collections import deque

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import IO_THRESHOLDS

# ── Style constants ───────────────────────────────────────────────────────────
CARD_BG     = "#500000"
CARD_BORDER = "#7a1515"
SECTION_BG  = "#1a0000"
TEXT_COLOR  = "#ffffff"
DIM_COLOR   = "#aaaaaa"
GRAPH_BG    = "#1a0000"
ALARM_COLOR = "#cc2222"
WARN_COLOR  = "#c8820a"
OK_COLOR    = "#4caf50"

SCROLL_SECS = 60
MAX_PTS     = 300

# Rated maximums per rail (for utilization bar)
RAIL_MAX_WATTS = {
    "relay1": 24 * 14,    # 24V @ 14A alarm threshold
    "relay2": 24 * 6,     # 24V @ 6A alarm threshold
    "24v":    24 * 6.5,   # 24V @ 6.5A alarm threshold
    "12v":    12 * 13,    # 12V @ 13A alarm threshold
}

RAIL_COLORS = {
    "relay1": "#ff6b6b",
    "relay2": "#ffa94d",
    "24v":    "#4dabf7",
    "12v":    "#69db7c",
}


def _card_style(border_color=CARD_BORDER):
    return (
        f"background-color:{CARD_BG};"
        f"border:1px solid {border_color};"
        f"border-radius:6px;"
    )


def section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
    lbl.setStyleSheet(f"color:{DIM_COLOR}; padding:4px 0 2px 4px;")
    return lbl


def _threshold_color(v_key, a_key, voltage, current):
    """Return colour based on worst threshold breach across V and A."""
    def worst(key, val):
        t = IO_THRESHOLDS.get(key)
        if t is None:
            return 0
        if val <= t["low_alarm"] or val >= t["high_alarm"]:
            return 2
        if val <= t["low_warn"] or val >= t["high_warn"]:
            return 1
        return 0
    level = max(worst(v_key, voltage), worst(a_key, current))
    return [OK_COLOR, WARN_COLOR, ALARM_COLOR][level]


# ── Scrolling watt graph ──────────────────────────────────────────────────────
class WattGraph(FigureCanvas):

    def __init__(self, color: str, max_w: float, parent=None):
        self._max_w = max_w
        fig = Figure(figsize=(3, 1.4), facecolor=GRAPH_BG, tight_layout=True)
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._ax = fig.add_subplot(111)
        ax = self._ax
        ax.set_facecolor(GRAPH_BG)
        ax.tick_params(colors="#888888", labelsize=7)
        ax.spines[:].set_color("#555555")
        ax.set_ylabel("W", color=DIM_COLOR, fontsize=8)
        ax.set_xlabel("seconds ago", color=DIM_COLOR, fontsize=7)
        ax.set_ylim(0, max_w * 1.1)
        ax.set_xlim(-SCROLL_SECS, 0)
        ax.grid(True, color="#333333", linewidth=0.5, linestyle=":")
        ax.axhline(max_w, color=ALARM_COLOR, lw=0.8, ls="--")

        self._line, = ax.plot([], [], color=color, linewidth=1.5)
        self._fill  = None

        self._times: deque = deque(maxlen=MAX_PTS)
        self._vals:  deque = deque(maxlen=MAX_PTS)
        self._t0 = time.time()

    def push(self, watts: float):
        self._times.append(time.time() - self._t0)
        self._vals.append(watts)
        self._redraw()

    def _redraw(self):
        if not self._times:
            return
        now = time.time() - self._t0
        xs = [t - now for t in self._times]
        ys = list(self._vals)
        self._line.set_data(xs, ys)
        self._ax.set_xlim(-SCROLL_SECS, 0)
        if ys:
            hi = max(ys)
            self._ax.set_ylim(0, max(self._max_w * 1.1, hi * 1.15))
        self.draw_idle()

    def tick(self):
        if self._times:
            self._redraw()


# ── Per-rail card ─────────────────────────────────────────────────────────────
class RailCard(QWidget):

    def __init__(self, rail_key: str, label: str,
                 v_key: str, a_key: str, parent=None):
        super().__init__(parent)
        self._rail_key = rail_key
        self._v_key    = v_key
        self._a_key    = a_key
        self._voltage  = 0.0
        self._current  = 0.0
        self._color    = RAIL_COLORS[rail_key]
        self._max_w    = RAIL_MAX_WATTS[rail_key]

        self.setStyleSheet(_card_style())
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)

        # Title
        title = QLabel(label)
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color:{self._color}; background:transparent; border:none;")
        lay.addWidget(title)

        # V / A / W row
        vals_row = QHBoxLayout()
        vals_row.setSpacing(12)

        self._v_lbl = self._make_val_lbl("— V")
        self._a_lbl = self._make_val_lbl("— A")
        self._w_lbl = self._make_val_lbl("— W")
        for lbl in [self._v_lbl, self._a_lbl, self._w_lbl]:
            vals_row.addWidget(lbl)
        vals_row.addStretch()
        lay.addLayout(vals_row)

        # Utilization bar
        util_row = QHBoxLayout()
        util_lbl = QLabel("Load:")
        util_lbl.setFont(QFont("Segoe UI", 8))
        util_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        util_row.addWidget(util_lbl)

        self._util_bar = QProgressBar()
        self._util_bar.setRange(0, 100)
        self._util_bar.setValue(0)
        self._util_bar.setFixedHeight(10)
        self._util_bar.setTextVisible(False)
        self._util_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2a0000;
                border: 1px solid {CARD_BORDER};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 3px;
            }}
        """)
        util_row.addWidget(self._util_bar, stretch=1)

        self._util_pct = QLabel("0%")
        self._util_pct.setFont(QFont("Segoe UI", 8))
        self._util_pct.setFixedWidth(36)
        self._util_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._util_pct.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        util_row.addWidget(self._util_pct)
        lay.addLayout(util_row)

        # Watt graph
        self._graph = WattGraph(self._color, self._max_w)
        lay.addWidget(self._graph, stretch=1)

    def _make_val_lbl(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        return lbl

    def update_values(self, voltage: float, current: float):
        self._voltage = voltage
        self._current = current
        watts = voltage * current
        color = _threshold_color(self._v_key, self._a_key, voltage, current)

        self._v_lbl.setText(f"{voltage:.1f} V")
        self._a_lbl.setText(f"{current:.2f} A")
        self._w_lbl.setText(f"{watts:.1f} W")
        for lbl in [self._v_lbl, self._a_lbl, self._w_lbl]:
            lbl.setStyleSheet(f"color:{color}; background:transparent; border:none;")

        pct = min(100, int(watts / self._max_w * 100))
        self._util_bar.setValue(pct)
        self._util_pct.setText(f"{pct}%")

        bar_color = OK_COLOR if pct < 75 else (WARN_COLOR if pct < 90 else ALARM_COLOR)
        self._util_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2a0000;
                border: 1px solid {CARD_BORDER};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
        """)

        self._graph.push(watts)

    def tick(self):
        self._graph.tick()


# ── 120VAC pump indicator ─────────────────────────────────────────────────────
class PumpIndicator(QWidget):
    """Shows whether Relay_1 CH7/8 (120VAC liquid injection pump) is energised."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on = False
        self.setStyleSheet(_card_style())
        self.setFixedHeight(90)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        self._dot = QLabel("●")
        self._dot.setFont(QFont("Segoe UI", 28))
        self._dot.setStyleSheet(f"color:#555555; background:transparent; border:none;")
        lay.addWidget(self._dot)

        txt = QVBoxLayout()
        title = QLabel("120VAC Liquid Injection Pump")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color:{TEXT_COLOR}; background:transparent; border:none;")
        txt.addWidget(title)

        self._status = QLabel("Relay_1 CH7/8 — OPEN (de-energised)")
        self._status.setFont(QFont("Segoe UI", 10))
        self._status.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        txt.addWidget(self._status)

        sub = QLabel("No power metering — relay state only")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet(f"color:#666666; background:transparent; border:none;")
        txt.addWidget(sub)

        lay.addLayout(txt)
        lay.addStretch()

    def set_pump_on(self, on: bool):
        self._on = on
        if on:
            self._dot.setStyleSheet(f"color:{OK_COLOR}; background:transparent; border:none;")
            self._status.setText("Relay_1 CH7/8 — CLOSED (energised)")
            self._status.setStyleSheet(f"color:{OK_COLOR}; background:transparent; border:none;")
        else:
            self._dot.setStyleSheet(f"color:#555555; background:transparent; border:none;")
            self._status.setText("Relay_1 CH7/8 — OPEN (de-energised)")
            self._status.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")


# ── Power Tab ─────────────────────────────────────────────────────────────────
class PowerTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{SECTION_BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # 120VAC pump indicator at the top
        root.addWidget(section_label("120VAC Circuit"))
        self.pump_indicator = PumpIndicator()
        root.addWidget(self.pump_indicator)

        # 4 DC rail cards in a row
        root.addWidget(section_label("DC Power Rails"))
        rails_row = QHBoxLayout()
        rails_row.setSpacing(8)

        self._rail_cards = {}
        for key, label, v_key, a_key in [
            ("relay1", "Relay 1",    "Relay1_V", "Relay1_A"),
            ("relay2", "Relay 2",    "Relay2_V", "Relay2_A"),
            ("24v",    "24V Supply", "Rail24V_V", "Rail24V_A"),
            ("12v",    "12V Supply", "Rail12V_V", "Rail12V_A"),
        ]:
            card = RailCard(key, label, v_key, a_key)
            self._rail_cards[key] = card
            rails_row.addWidget(card)

        root.addLayout(rails_row, stretch=1)

        # Refresh timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_power(self, key: str, voltage: float, current: float):
        """key = 'relay1' | 'relay2' | '24v' | '12v'"""
        if key in self._rail_cards:
            self._rail_cards[key].update_values(voltage, current)

    def set_pump_state(self, on: bool):
        """Called when Relay_1 CH7 or CH8 state is read from Modbus."""
        self.pump_indicator.set_pump_on(on)

    def set_system_state(self, state: str):
        pass

    def _tick(self):
        for card in self._rail_cards.values():
            card.tick()
