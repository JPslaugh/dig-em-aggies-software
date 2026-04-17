#!/usr/bin/env python3
"""
Water Flow Monitor for pi-claw
Dig 'Em Aggies – Not-a-Boring Competition 2026

Hardware: Digiten FL-608 flow sensor on GPIO 17
  - Red  → Pin 2  (5V)
  - Black → Pin 6  (GND)
  - Yellow → Pin 11 (GPIO 17, internal pull-up enabled)

Calibration: F = 7.5 * Q (L/min) → 450 pulses/liter
  This is the factory spec. Adjust PULSES_PER_LITER if real-world
  testing shows a different value.

Sensor status: considered ACTIVE if at least one pulse has been
  received in the last 2 seconds.

Run: WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000
     QT_QPA_PLATFORM=wayland python3 flow_monitor.py
"""

import sys
import time
import threading
import RPi.GPIO as GPIO
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QFrame, QPushButton)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor

# ── Sensor config ────────────────────────────────────────────────────────────
GPIO_PIN         = 17
PULSES_PER_LITER = 450.0   # FL-608 factory spec (F=7.5*Q). Adjust after calibration.

# ── Shared state ─────────────────────────────────────────────────────────────
_lock            = threading.Lock()
_pulse_count     = 0       # total pulses since start (for total liters)
_pulses_this_sec = 0       # pulses counted in current 1-second window
_flow_rate       = 0.0     # L/min, updated every second
_total_liters    = 0.0     # cumulative liters since start
_last_pulse_time = 0.0     # timestamp of last pulse (for active detection)

def _pulse_callback(channel):
    global _pulse_count, _pulses_this_sec, _last_pulse_time
    with _lock:
        _pulse_count     += 1
        _pulses_this_sec += 1
        _last_pulse_time  = time.time()

def _flow_calc_loop():
    """Updates flow rate and total liters once per second from pulse counts."""
    global _pulses_this_sec, _flow_rate, _total_liters
    while True:
        time.sleep(1.0)
        with _lock:
            hz              = _pulses_this_sec        # pulses in last second = Hz
            _flow_rate      = hz / 7.5               # Q = F / 7.5  (L/min)
            _total_liters  += _pulses_this_sec / PULSES_PER_LITER
            _pulses_this_sec = 0

def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(GPIO_PIN, GPIO.FALLING,
                          callback=_pulse_callback, bouncetime=2)
    threading.Thread(target=_flow_calc_loop, daemon=True).start()

# ── UI helpers ───────────────────────────────────────────────────────────────
class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 8px;
            }
        """)

class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("background-color: #444444; max-height: 2px; border: none;")

class GraphWidget(QWidget):
    """Rolling line graph drawn with QPainter — no external libraries needed.
    Stores the last MAX_POINTS readings (sampled every 0.5 s = 60 s of history).
    """
    MAX_POINTS = 120  # 120 × 0.5 s = 60 seconds

    def __init__(self, label, unit, line_color="#42a5f5"):
        super().__init__()
        self.label      = label
        self.unit       = unit
        self.line_color = line_color
        self.data       = []
        self.setStyleSheet(
            "background-color: #2c2c2c; border: 1px solid #444444; border-radius: 8px;"
        )

    def add_point(self, value):
        self.data.append(float(value))
        if len(self.data) > self.MAX_POINTS:
            self.data.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        ml, mr, mt, mb = 46, 8, 18, 20
        gw = w - ml - mr
        gh = h - mt - mb

        painter.fillRect(0, 0, w, h, QColor("#2c2c2c"))

        painter.setPen(QColor("#9e9e9e"))
        painter.setFont(QFont("Sans", 8, QFont.Bold))
        painter.drawText(ml, 13, f"{self.label}  ({self.unit})")

        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawLine(ml, mt, ml, mt + gh)
        painter.drawLine(ml, mt + gh, ml + gw, mt + gh)

        n = len(self.data)
        if n < 2:
            painter.end()
            return

        mn = min(self.data)
        mx = max(self.data)
        if abs(mx - mn) < 0.001:
            mx = mn + 1.0

        for i in range(4):
            frac = i / 3.0
            y    = mt + int(gh * frac)
            val  = mx - (mx - mn) * frac

            painter.setPen(QPen(QColor("#383838"), 1, Qt.DotLine))
            painter.drawLine(ml + 1, y, ml + gw, y)

            painter.setPen(QColor("#7a7a7a"))
            painter.setFont(QFont("Sans", 7))
            painter.drawText(0, y - 7, ml - 3, 14,
                             Qt.AlignRight | Qt.AlignVCenter, f"{val:.2f}")

        secs = int(n * 0.5)
        painter.setPen(QColor("#7a7a7a"))
        painter.setFont(QFont("Sans", 7))
        painter.drawText(ml, h - 3, f"{min(secs, 60)}s ago")
        painter.drawText(ml + gw - 26, h - 3, "now")

        painter.setPen(QPen(QColor(self.line_color), 2))
        for i in range(1, n):
            x1 = ml + int(gw * (i - 1) / max(n - 1, 1))
            x2 = ml + int(gw * i       / max(n - 1, 1))
            y1 = mt + gh - int(gh * (self.data[i - 1] - mn) / (mx - mn))
            y2 = mt + gh - int(gh * (self.data[i]     - mn) / (mx - mn))
            painter.drawLine(x1, y1, x2, y2)

        painter.end()

# ── Main window ───────────────────────────────────────────────────────────────
class FlowMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Monitor – Dig 'Em Aggies")
        self.setStyleSheet("background-color: #1a1a1a;")
        self.resize(900, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)

        # Title
        title = QLabel("DIG 'EM AGGIES  —  FLOW MONITOR")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Sans", 20, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)
        layout.addWidget(Separator())

        # ── Top row: Sensor | Flow rate | Total volume ────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Sensor status card
        status_card = Card()
        sl = QVBoxLayout()
        sl.setSpacing(3)
        status_lbl = QLabel("SENSOR")
        status_lbl.setFont(QFont("Sans", 13, QFont.Bold))
        status_lbl.setStyleSheet("color: #9e9e9e; border: none;")
        status_lbl.setAlignment(Qt.AlignCenter)
        self.status_val = QLabel("CHECKING...")
        self.status_val.setFont(QFont("Sans", 18, QFont.Bold))
        self.status_val.setStyleSheet("color: gray; border: none;")
        self.status_val.setAlignment(Qt.AlignCenter)
        sl.addWidget(status_lbl)
        sl.addWidget(self.status_val)
        status_card.setLayout(sl)
        top_row.addWidget(status_card, stretch=1)

        # Flow rate card
        flow_card = Card()
        fl = QVBoxLayout()
        fl.setSpacing(1)
        flow_lbl = QLabel("FLOW RATE")
        flow_lbl.setFont(QFont("Sans", 13, QFont.Bold))
        flow_lbl.setStyleSheet("color: #9e9e9e; border: none;")
        flow_lbl.setAlignment(Qt.AlignCenter)
        self.flow_val = QLabel("0.00")
        self.flow_val.setFont(QFont("Sans", 40, QFont.Bold))
        self.flow_val.setStyleSheet("color: #e0e0e0; border: none;")
        self.flow_val.setAlignment(Qt.AlignCenter)
        flow_unit = QLabel("liters / min")
        flow_unit.setFont(QFont("Sans", 12))
        flow_unit.setStyleSheet("color: #9e9e9e; border: none;")
        flow_unit.setAlignment(Qt.AlignCenter)
        fl.addWidget(flow_lbl)
        fl.addWidget(self.flow_val)
        fl.addWidget(flow_unit)
        flow_card.setLayout(fl)
        top_row.addWidget(flow_card, stretch=2)

        # Total volume card
        total_card = Card()
        tl = QVBoxLayout()
        tl.setSpacing(3)
        total_lbl = QLabel("TOTAL VOLUME")
        total_lbl.setFont(QFont("Sans", 13, QFont.Bold))
        total_lbl.setStyleSheet("color: #9e9e9e; border: none;")
        total_lbl.setAlignment(Qt.AlignCenter)
        self.total_val = QLabel("0.000")
        self.total_val.setFont(QFont("Sans", 28, QFont.Bold))
        self.total_val.setStyleSheet("color: #e0e0e0; border: none;")
        self.total_val.setAlignment(Qt.AlignCenter)
        total_unit = QLabel("liters")
        total_unit.setFont(QFont("Sans", 12))
        total_unit.setStyleSheet("color: #9e9e9e; border: none;")
        total_unit.setAlignment(Qt.AlignCenter)
        tl.addWidget(total_lbl)
        tl.addWidget(self.total_val)
        tl.addWidget(total_unit)
        total_card.setLayout(tl)
        top_row.addWidget(total_card, stretch=2)

        layout.addLayout(top_row)

        # ── Graphs ────────────────────────────────────────────────────────────
        graphs_row = QHBoxLayout()
        graphs_row.setSpacing(10)
        self.flow_graph  = GraphWidget("Flow Rate",    "L/min", "#42a5f5")
        self.total_graph = GraphWidget("Total Volume", "L",     "#26c6da")
        graphs_row.addWidget(self.flow_graph,  stretch=1)
        graphs_row.addWidget(self.total_graph, stretch=1)
        layout.addLayout(graphs_row, stretch=1)

        # ── Reset button ──────────────────────────────────────────────────────
        self.reset_btn = QPushButton("RESET TOTAL")
        self.reset_btn.setFont(QFont("Sans", 13, QFont.Bold))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                color: #9e9e9e;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_total)
        layout.addWidget(self.reset_btn)

    def reset_total(self):
        global _total_liters, _pulse_count
        with _lock:
            _total_liters = 0.0
            _pulse_count  = 0
        self.total_graph.data.clear()
        self.total_graph.update()

    def update_ui(self):
        with _lock:
            flow   = _flow_rate
            total  = _total_liters
            last_t = _last_pulse_time

        active = (time.time() - last_t) < 2.0 if last_t > 0 else False

        if active:
            self.status_val.setText("ACTIVE")
            self.status_val.setStyleSheet("color: #66bb6a; border: none;")
        else:
            self.status_val.setText("NO FLOW")
            self.status_val.setStyleSheet("color: #ef5350; border: none;")

        self.flow_val.setText(f"{flow:.2f}")
        if flow > 10:
            self.flow_val.setStyleSheet("color: #66bb6a; border: none;")
        elif flow > 0.1:
            self.flow_val.setStyleSheet("color: #ffa726; border: none;")
        else:
            self.flow_val.setStyleSheet("color: #e0e0e0; border: none;")

        self.total_val.setText(f"{total:.3f}")

        self.flow_graph.add_point(flow)
        self.total_graph.add_point(total)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, 'timer'):
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_ui)
            self.timer.start(500)


def main():
    init_gpio()
    app = QApplication(sys.argv)
    w = FlowMonitor()
    w.show()
    try:
        sys.exit(app.exec_())
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
