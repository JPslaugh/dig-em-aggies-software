"""
Machine State Tab
Left   : TBM attitude visualizer (roll/pitch artificial horizon + yaw compass)
         + depth gauge
Middle : Scrolling time-series graphs — Depth, RPM, Flow
Right  : Live numeric readouts for all machine sensors
"""

import math
import time
from collections import deque

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import (
    QFont, QPainter, QColor, QPen, QBrush, QPainterPath,
    QLinearGradient, QRadialGradient
)

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

from config import IO_THRESHOLDS, State

CARD_BG     = "#500000"
CARD_BORDER = "#7a1515"
SECTION_BG  = "#1a0000"
TEXT_COLOR  = "#ffffff"
DIM_COLOR   = "#aaaaaa"

GRAPH_BG    = "#1a0000"
GRAPH_LINE  = {"Depth": "#4a9eff", "RPM": "#ff9c4a", "Flow": "#4cff9c"}
GRAPH_ALARM = "#cc2222"
GRAPH_WARN  = "#c8820a"

SCROLL_SECS = 60   # seconds of history shown on graphs
MAX_PTS     = 300  # max data points kept


def _card_style():
    return (
        f"background-color:{CARD_BG};"
        f"border:1px solid {CARD_BORDER};"
        f"border-radius:6px;"
    )


def section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
    lbl.setStyleSheet(f"color:{DIM_COLOR}; padding:4px 0 2px 4px;")
    return lbl


class AttitudeWidget(QWidget):
    """Draws an artificial horizon for roll/pitch."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roll  = 0.0   # degrees, + = right wing down
        self._pitch = 0.0   # degrees, + = nose up
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_attitude(self, roll: float, pitch: float):
        self._roll  = roll
        self._pitch = pitch
        self.update()

    def paintEvent(self, _event):
        w, h = self.width(), self.height()
        r = min(w, h) / 2 - 6
        cx, cy = w / 2, h / 2

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Clip to circle
        clip = QPainterPath()
        clip.addEllipse(QPointF(cx, cy), r, r)
        p.setClipPath(clip)

        # Sky / ground — rotate by roll, shift by pitch
        pitch_px = (self._pitch / 90.0) * r
        p.save()
        p.translate(cx, cy)
        p.rotate(-self._roll)

        # Sky gradient
        sky = QLinearGradient(0, -r, 0, pitch_px)
        sky.setColorAt(0, QColor("#1a4a8a"))
        sky.setColorAt(1, QColor("#2a6abf"))
        p.fillRect(-int(r*2), -int(r*2), int(r*4), int(r*2 + pitch_px + 1), sky)

        # Ground gradient
        gnd = QLinearGradient(0, pitch_px, 0, r)
        gnd.setColorAt(0, QColor("#6b3a1f"))
        gnd.setColorAt(1, QColor("#3d1f0a"))
        p.fillRect(-int(r*2), int(pitch_px), int(r*4), int(r*2), gnd)

        # Horizon line
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.drawLine(int(-r*1.5), int(pitch_px), int(r*1.5), int(pitch_px))

        # Pitch ladder (every 10°)
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(QPen(QColor("#ffffff"), 1))
        for deg in range(-40, 50, 10):
            if deg == 0:
                continue
            y = pitch_px - (deg / 90.0) * r
            line_w = r * (0.3 if deg % 20 == 0 else 0.18)
            p.drawLine(int(-line_w), int(y), int(line_w), int(y))
            p.drawText(int(line_w + 4), int(y + 4), str(deg))

        p.restore()

        # Remove clip for outer ring
        p.setClipping(False)

        # Outer ring
        p.setPen(QPen(QColor(CARD_BORDER), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Roll arc tick marks
        p.setPen(QPen(QColor("#ffffff"), 1))
        for deg in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            rad = math.radians(deg - 90)
            inner = r - (8 if deg % 30 == 0 else 5)
            x1 = cx + r * math.cos(rad)
            y1 = cy + r * math.sin(rad)
            x2 = cx + inner * math.cos(rad)
            y2 = cy + inner * math.sin(rad)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Roll indicator triangle (points inward from top of arc)
        roll_rad = math.radians(-self._roll - 90)
        tri_tip  = r - 2
        tri_base = r - 14
        tx = cx + tri_tip  * math.cos(roll_rad)
        ty = cy + tri_tip  * math.sin(roll_rad)
        # perpendicular for base corners
        perp = math.radians(-self._roll - 90 + 90)
        bw = 6
        b1x = cx + tri_base * math.cos(roll_rad) + bw * math.cos(perp)
        b1y = cy + tri_base * math.sin(roll_rad) + bw * math.sin(perp)
        b2x = cx + tri_base * math.cos(roll_rad) - bw * math.cos(perp)
        b2y = cy + tri_base * math.sin(roll_rad) - bw * math.sin(perp)
        tri = QPainterPath()
        tri.moveTo(tx, ty)
        tri.lineTo(b1x, b1y)
        tri.lineTo(b2x, b2y)
        tri.closeSubpath()
        p.setPen(QPen(QColor("#ffdd44"), 1))
        p.setBrush(QBrush(QColor("#ffdd44")))
        p.drawPath(tri)

        # Fixed aircraft symbol
        p.setPen(QPen(QColor("#ffdd44"), 2))
        p.drawLine(int(cx - 30), int(cy), int(cx - 10), int(cy))
        p.drawLine(int(cx + 10), int(cy), int(cx + 30), int(cy))
        p.drawLine(int(cx - 5),  int(cy), int(cx + 5),  int(cy))
        p.drawLine(int(cx),  int(cy - 5), int(cx),  int(cy + 5))

        p.end()


class CompassWidget(QWidget):
    """Simple compass rose showing yaw/heading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._yaw = 0.0
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_yaw(self, yaw: float):
        self._yaw = yaw
        self.update()

    def paintEvent(self, _event):
        w, h = self.width(), self.height()
        r = min(w, h) / 2 - 6
        cx, cy = w / 2, h / 2

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Background circle
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#2a0000")))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Cardinal tick marks
        cardinals = {0: "N", 90: "E", 180: "S", 270: "W"}
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for deg in range(0, 360, 10):
            rad = math.radians(deg - self._yaw - 90)
            is_cardinal = deg % 90 == 0
            is_major    = deg % 30 == 0
            inner = r - (14 if is_cardinal else (9 if is_major else 5))
            x1 = cx + r * math.cos(rad)
            y1 = cy + r * math.sin(rad)
            x2 = cx + inner * math.cos(rad)
            y2 = cy + inner * math.sin(rad)
            color = "#ff4444" if deg == 0 else "#ffffff"
            p.setPen(QPen(QColor(color), 2 if is_major else 1))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
            if is_cardinal:
                lbl = cardinals[deg]
                lx = cx + (r - 22) * math.cos(rad)
                ly = cy + (r - 22) * math.sin(rad)
                p.setPen(QPen(QColor(color)))
                p.drawText(QRectF(lx - 10, ly - 10, 20, 20), Qt.AlignCenter, lbl)

        # Fixed lubber line (top = current heading)
        p.setPen(QPen(QColor("#ffdd44"), 2))
        p.drawLine(int(cx), int(cy - r + 2), int(cx), int(cy - r + 16))

        # Heading needle
        p.setPen(QPen(QColor("#ffdd44"), 2))
        p.setBrush(QBrush(QColor("#ffdd44")))
        needle = QPainterPath()
        needle.moveTo(cx, cy - r * 0.55)
        needle.lineTo(cx - 5, cy)
        needle.lineTo(cx + 5, cy)
        needle.closeSubpath()
        p.drawPath(needle)

        # Center dot
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QPointF(cx, cy), 4, 4)

        # Outer ring
        p.setPen(QPen(QColor(CARD_BORDER), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Yaw value text
        p.setPen(QPen(QColor(TEXT_COLOR)))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(QRectF(cx - 30, cy + r * 0.3, 60, 24), Qt.AlignCenter, f"{self._yaw:.1f}°")

        p.end()


class DepthGauge(QWidget):
    """Vertical bar showing current depth vs target (8 m)."""

    MAX_DEPTH = 8.0   # metres — from IO_THRESHOLDS high_alarm

    def __init__(self, parent=None):
        super().__init__(parent)
        self._depth = 0.0
        self.setMinimumSize(60, 180)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(80)

    def set_depth(self, depth: float):
        self._depth = max(0.0, depth)
        self.update()

    def paintEvent(self, _event):
        w, h = self.width(), self.height()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        bar_x = w // 2 - 12
        bar_w = 24
        bar_top = 20
        bar_h = h - 50

        # Background bar
        p.setPen(QPen(QColor(CARD_BORDER), 1))
        p.setBrush(QBrush(QColor("#2a0000")))
        p.drawRoundedRect(bar_x, bar_top, bar_w, bar_h, 4, 4)

        # Filled portion (depth goes DOWN — fill from top)
        frac = min(1.0, self._depth / self.MAX_DEPTH)
        fill_h = int(bar_h * frac)
        if fill_h > 0:
            grad = QLinearGradient(0, bar_top, 0, bar_top + bar_h)
            grad.setColorAt(0.0, QColor("#4a9eff"))
            grad.setColorAt(0.75, QColor("#2a6abf"))
            grad.setColorAt(1.0, QColor("#cc2222"))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(bar_x, bar_top, bar_w, fill_h, 4, 4)

        # Tick marks at 1m intervals
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(QPen(QColor(DIM_COLOR), 1))
        for m in range(0, int(self.MAX_DEPTH) + 1):
            y = bar_top + int((m / self.MAX_DEPTH) * bar_h)
            p.drawLine(bar_x - 4, y, bar_x, y)
            p.drawText(bar_x - 22, y + 4, f"{m}m")

        # Current depth label
        p.setPen(QPen(QColor(TEXT_COLOR)))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(QRectF(0, h - 28, w, 20), Qt.AlignCenter, f"{self._depth:.2f} m")

        # Title
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(QPen(QColor(DIM_COLOR)))
        p.drawText(QRectF(0, 2, w, 16), Qt.AlignCenter, "DEPTH")

        p.end()


class DerivedMetricsCard(QWidget):
    """Shows cutterhead acceleration, downward velocity, and total fluid volume."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        self._accel_lbl  = self._make_row(lay, "Cutterhead Accel", "RPM/s")
        self._vel_lbl    = self._make_row(lay, "Downward Velocity", "mm/s")
        self._vol_lbl    = self._make_row(lay, "Total Fluid Injected", "L")

    def _make_row(self, parent_lay, title: str, unit: str):
        row = QVBoxLayout()
        row.setSpacing(1)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 9))
        title_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        row.addWidget(title_lbl)

        val_row = QHBoxLayout()
        val_lbl = QLabel("—")
        val_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        val_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        val_row.addWidget(val_lbl)

        unit_lbl = QLabel(unit)
        unit_lbl.setFont(QFont("Segoe UI", 10))
        unit_lbl.setAlignment(Qt.AlignBottom)
        unit_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        val_row.addWidget(unit_lbl)
        val_row.addStretch()
        row.addLayout(val_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{CARD_BORDER};")

        parent_lay.addLayout(row)
        parent_lay.addWidget(sep)
        return val_lbl

    def update_accel(self, val: float):
        color = "#cc2222" if abs(val) > 50 else "#4caf50"
        self._accel_lbl.setText(f"{val:+.1f}")
        self._accel_lbl.setStyleSheet(f"color:{color}; background:transparent; border:none;")

    def update_velocity(self, val_ms: float):
        # Convert m/s to mm/s for display
        val_mms = val_ms * 1000
        color = "#c8820a" if val_mms < 0 else "#4caf50"
        self._vel_lbl.setText(f"{val_mms:.2f}")
        self._vel_lbl.setStyleSheet(f"color:{color}; background:transparent; border:none;")

    def update_volume(self, val_L: float):
        self._vol_lbl.setText(f"{val_L:.2f}")
        self._vol_lbl.setStyleSheet(f"color:{TEXT_COLOR}; background:transparent; border:none;")


class ScrollingGraph(FigureCanvas):
    """Single-metric scrolling graph with warn/alarm bands."""

    def __init__(self, key: str, label: str, unit: str, color: str,
                 y_min: float = 0, y_max: float = 100, parent=None):
        self._key   = key
        self._label = label
        self._unit  = unit
        self._color = color
        self._y_min = y_min
        self._y_max = y_max

        fig = Figure(figsize=(3, 1.8), facecolor=GRAPH_BG, tight_layout=True)
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._ax = fig.add_subplot(111)
        self._setup_axes()

        self._times: deque = deque(maxlen=MAX_PTS)
        self._vals:  deque = deque(maxlen=MAX_PTS)
        self._t0 = time.time()

        self._line, = self._ax.plot([], [], color=color, linewidth=1.5)

        # Threshold bands
        t = IO_THRESHOLDS.get(key, {})
        if t:
            lw = dict(lw=0.6, ls="--")
            if t["high_warn"]  < y_max: self._ax.axhline(t["high_warn"],  color=GRAPH_WARN,  **lw)
            if t["high_alarm"] < y_max: self._ax.axhline(t["high_alarm"], color=GRAPH_ALARM, **lw)
            if t["low_warn"]   > y_min: self._ax.axhline(t["low_warn"],   color=GRAPH_WARN,  **lw)
            if t["low_alarm"]  > y_min: self._ax.axhline(t["low_alarm"],  color=GRAPH_ALARM, **lw)

    def _setup_axes(self):
        ax = self._ax
        ax.set_facecolor(GRAPH_BG)
        ax.tick_params(colors="#888888", labelsize=7)
        ax.spines[:].set_color("#555555")
        ax.set_ylabel(f"{self._label} ({self._unit})", color=DIM_COLOR, fontsize=8)
        ax.set_xlabel("seconds ago", color=DIM_COLOR, fontsize=7)
        ax.set_ylim(self._y_min, self._y_max)
        ax.set_xlim(-SCROLL_SECS, 0)
        ax.yaxis.label.set_color(DIM_COLOR)
        ax.grid(True, color="#333333", linewidth=0.5, linestyle=":")

    def push(self, value: float):
        now = time.time() - self._t0
        self._times.append(now)
        self._vals.append(value)
        self._redraw()

    def _redraw(self):
        if not self._times:
            return
        now = self._times[-1]
        xs = [t - now for t in self._times]
        self._line.set_data(xs, list(self._vals))
        self._ax.set_xlim(-SCROLL_SECS, 0)
        # Dynamic y expansion
        if self._vals:
            lo = min(self._vals)
            hi = max(self._vals)
            pad = (hi - lo) * 0.1 or 1
            self._ax.set_ylim(
                min(self._y_min, lo - pad),
                max(self._y_max, hi + pad)
            )
        self.draw_idle()


class ReadoutCard(QWidget):
    """Small card: label + big value + unit + status colour."""

    def __init__(self, title: str, unit: str, parent=None):
        super().__init__(parent)
        self._key = title
        self.setStyleSheet(_card_style())
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        self._title = QLabel(title)
        self._title.setFont(QFont("Segoe UI", 9))
        self._title.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        lay.addWidget(self._title)

        self._val = QLabel("—")
        self._val.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._val.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        lay.addWidget(self._val)

        self._unit_lbl = QLabel(unit)
        self._unit_lbl.setFont(QFont("Segoe UI", 9))
        self._unit_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        lay.addWidget(self._unit_lbl)

    def update_value(self, value: float, color: str = TEXT_COLOR):
        self._val.setText(f"{value:.1f}")
        self._val.setStyleSheet(f"color:{color}; background:transparent; border:none;")


class MachineStateTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{SECTION_BG};")

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(8)

        left.addWidget(section_label("Orientation"))

        att_card = QWidget()
        att_card.setStyleSheet(_card_style())
        att_lay = QVBoxLayout(att_card)
        att_lay.setContentsMargins(8, 8, 8, 8)
        att_lay.setSpacing(4)

        self.attitude = AttitudeWidget()
        att_lay.addWidget(self.attitude, stretch=3)

        # Roll / Pitch labels under horizon
        rp_row = QHBoxLayout()
        self._roll_lbl  = QLabel("Roll: 0.0°")
        self._pitch_lbl = QLabel("Pitch: 0.0°")
        for lbl in [self._roll_lbl, self._pitch_lbl]:
            lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{TEXT_COLOR}; background:transparent; border:none;")
            rp_row.addWidget(lbl)
        att_lay.addLayout(rp_row)

        left.addWidget(att_card, stretch=3)

        left.addWidget(section_label("Yaw / Heading"))
        yaw_card = QWidget()
        yaw_card.setStyleSheet(_card_style())
        yaw_lay = QVBoxLayout(yaw_card)
        yaw_lay.setContentsMargins(8, 8, 8, 8)
        self.compass = CompassWidget()
        yaw_lay.addWidget(self.compass)
        left.addWidget(yaw_card, stretch=2)

        left.addWidget(section_label("Derived"))
        self.derived = DerivedMetricsCard()
        left.addWidget(self.derived, stretch=2)

        root.addLayout(left, stretch=3)

        mid = QVBoxLayout()
        mid.setSpacing(8)
        mid.addWidget(section_label("Sensor History (last 60 s)"))

        t = IO_THRESHOLDS
        self.graph_depth = ScrollingGraph(
            "Depth", "Depth", "m",      GRAPH_LINE["Depth"],
            y_min=0, y_max=t["Depth"]["high_alarm"]
        )
        self.graph_rpm   = ScrollingGraph(
            "RPM",   "RPM",   "RPM",    GRAPH_LINE["RPM"],
            y_min=0, y_max=t["RPM"]["high_alarm"]
        )
        self.graph_flow  = ScrollingGraph(
            "Flow",  "Flow",  "L/min",  GRAPH_LINE["Flow"],
            y_min=0, y_max=t["Flow"]["high_alarm"]
        )

        for g in [self.graph_depth, self.graph_rpm, self.graph_flow]:
            mid.addWidget(g, stretch=1)

        root.addLayout(mid, stretch=4)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(section_label("Live Readings"))

        self._readouts = {}
        sensors = [
            ("RPM",        "Cutterhead RPM", "RPM"),
            ("Flow",       "Flow Rate",      "L/min"),
            ("Depth",      "Bore Depth",     "m"),
            ("Roll",       "Roll",           "°"),
            ("Pitch",      "Pitch",          "°"),
            ("Yaw",        "Yaw / Heading",  "°"),
            ("Encl_Temp1", "Encl Temp 1",    "°C"),
            ("Encl_Temp2", "Encl Temp 2",    "°C"),
        ]
        for key, title, unit in sensors:
            card = ReadoutCard(title, unit)
            self._readouts[key] = card
            right.addWidget(card)

        right.addStretch()
        root.addLayout(right, stretch=2)

        # Derived metric state
        self._prev_rpm   = None
        self._prev_rpm_t = None
        self._prev_depth   = None
        self._prev_depth_t = None
        self._total_volume = 0.0      # litres
        self._prev_flow    = None
        self._prev_flow_t  = None

        # Refresh timer — redraws graphs & stale checks
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)


    def update_sensor(self, key: str, value: float):
        """Called by MainWindow whenever a Teensy sensor value arrives."""
        from config import IO_THRESHOLDS
        t = IO_THRESHOLDS.get(key, {})

        def _color(v):
            if not t:
                return TEXT_COLOR
            if v <= t["low_alarm"] or v >= t["high_alarm"]:
                return "#cc2222"
            if v <= t["low_warn"]  or v >= t["high_warn"]:
                return "#c8820a"
            return "#4caf50"

        if key in self._readouts:
            self._readouts[key].update_value(value, _color(value))

        if key == "Roll":
            self._roll_lbl.setText(f"Roll: {value:+.1f}°")
            self.attitude.set_attitude(value, self._current_pitch())
        elif key == "Pitch":
            self._pitch_lbl.setText(f"Pitch: {value:+.1f}°")
            self.attitude.set_attitude(self._current_roll(), value)
        elif key == "Yaw":
            self.compass.set_yaw(value)
        elif key == "Depth":
            self.graph_depth.push(value)
            now = time.time()
            if self._prev_depth is not None and self._prev_depth_t is not None:
                dt = now - self._prev_depth_t
                if dt > 0:
                    velocity = (value - self._prev_depth) / dt  # m/s
                    self.derived.update_velocity(velocity)
            self._prev_depth   = value
            self._prev_depth_t = now
        elif key == "RPM":
            self.graph_rpm.push(value)
            now = time.time()
            if self._prev_rpm is not None and self._prev_rpm_t is not None:
                dt = now - self._prev_rpm_t
                if dt > 0:
                    accel = (value - self._prev_rpm) / dt  # RPM/s
                    self.derived.update_accel(accel)
            self._prev_rpm   = value
            self._prev_rpm_t = now
        elif key == "Flow":
            self.graph_flow.push(value)
            now = time.time()
            if self._prev_flow is not None and self._prev_flow_t is not None:
                dt = now - self._prev_flow_t
                if dt > 0:
                    # flow in L/min → integrate to get L
                    self._total_volume += value * (dt / 60.0)
                    self.derived.update_volume(self._total_volume)
            self._prev_flow   = value
            self._prev_flow_t = now

    def set_system_state(self, state: str):
        pass  # reserved for future state-dependent UI changes


    def _current_roll(self) -> float:
        txt = self._roll_lbl.text().replace("Roll: ", "").replace("°", "")
        try:
            return float(txt)
        except ValueError:
            return 0.0

    def _current_pitch(self) -> float:
        txt = self._pitch_lbl.text().replace("Pitch: ", "").replace("°", "")
        try:
            return float(txt)
        except ValueError:
            return 0.0

    def _tick(self):
        """Periodic graph refresh — keeps time axis scrolling even with no new data."""
        for g in [self.graph_depth, self.graph_rpm, self.graph_flow]:
            if g._times:
                g._redraw()
