#!/usr/bin/env python3
"""
Relay Control Panel - Dig 'Em Aggies
Not-a-Boring Competition 2026

Controls 2x Waveshare Modbus POE ETH Relay 16CH boards:
  Relay_1: 192.168.100.10
  Relay_2: 192.168.100.11

Dependencies: python3-pyqt5, pymodbus
Run: python3 relay_control.py
"""

import sys
import threading
import logging
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QFrame, QPushButton, QTabWidget, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from pymodbus.client import ModbusTcpClient

logging.getLogger("pymodbus").setLevel(logging.CRITICAL)

RELAY_BOARDS = [
    {
        "name": "Relay_1",
        "ip": "192.168.100.10",
        "port": 502,
        "labels": {},  # No labels yet — harmful devices TBD
    },
    {
        "name": "Relay_2",
        "ip": "192.168.100.11",
        "port": 502,
        "labels": {
            0: "Green Light",
            1: "Yellow Light",
            2: "Red Light",
            3: "Alarm",
            4: "Ground Power",
        },
    },
]

NUM_CHANNELS = 16


# ── Modbus board wrapper ──────────────────────────────────────────────────────

class RelayBoard:
    """Thread-safe Modbus TCP wrapper for a single relay board."""

    def __init__(self, ip, port=502):
        self.ip = ip
        self.port = port
        self._lock = threading.Lock()
        self._client = None
        self._connected = False
        self._states = [False] * NUM_CHANNELS

    def connect(self):
        try:
            self._client = ModbusTcpClient(host=self.ip, port=self.port)
            self._connected = self._client.connect()
        except Exception:
            self._connected = False
        return self._connected

    def disconnect(self):
        if self._client:
            self._client.close()
        self._connected = False

    @property
    def connected(self):
        return self._connected

    def read_states(self):
        """Read all 16 relay states. Returns list[bool] or None on error."""
        with self._lock:
            if not self._connected:
                return None
            try:
                result = self._client.read_coils(0, count=16)
                if result and not result.isError():
                    self._states = list(result.bits[:16])
                    return self._states
            except Exception:
                self._connected = False
            return None

    def set_relay(self, channel, state):
        """Set a single relay (0-indexed). Returns True on success."""
        with self._lock:
            if not self._connected:
                return False
            try:
                result = self._client.write_coil(channel, state)
                if not result.isError():
                    self._states[channel] = state
                    return True
            except Exception:
                self._connected = False
            return False

    def set_all(self, state):
        """Set all 16 relays at once. Returns True on success."""
        with self._lock:
            if not self._connected:
                return False
            try:
                result = self._client.write_coil(0xFF, state)
                if not result.isError():
                    self._states = [state] * NUM_CHANNELS
                    return True
            except Exception:
                self._connected = False
            return False


# ── UI helpers ────────────────────────────────────────────────────────────────

class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("background-color: #444444; max-height: 2px; border: none;")


class RelayButton(QPushButton):
    """Toggle button for a single relay channel."""

    def __init__(self, channel, label=None):
        super().__init__()
        self.channel = channel
        self.label = label
        self.is_on = False
        self.setFont(QFont("Sans", 9, QFont.Bold))
        self.setFixedSize(88, 64)
        self._refresh()

    def set_state(self, state):
        if self.is_on != state:
            self.is_on = state
            self._refresh()

    def _refresh(self):
        top = self.label if self.label else f"CH {self.channel + 1:02d}"
        self.setText(f"{top}\n{'ON' if self.is_on else 'OFF'}")
        if self.is_on:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    color: #a5d6a7;
                    border: 2px solid #66bb6a;
                    border-radius: 8px;
                }
                QPushButton:pressed { background-color: #388e3c; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2c2c2c;
                    color: #757575;
                    border: 2px solid #555555;
                    border-radius: 8px;
                }
                QPushButton:pressed { background-color: #3a3a3a; }
            """)


# ── Board tab ─────────────────────────────────────────────────────────────────

class BoardTab(QWidget):
    """Tab showing all 16 relay channels for one board."""

    def __init__(self, board: RelayBoard, name: str, labels: dict):
        super().__init__()
        self.board = board
        self.name = name
        self.labels = labels
        self.buttons: list[RelayButton] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel("CONNECTING...")
        self.status_label.setFont(QFont("Sans", 11, QFont.Bold))
        self.status_label.setStyleSheet("color: #ffa726;")
        ip_label = QLabel(f"{self.board.ip}:{self.board.port}")
        ip_label.setFont(QFont("Sans", 10))
        ip_label.setStyleSheet("color: #616161;")
        ip_label.setAlignment(Qt.AlignRight)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(ip_label)
        layout.addLayout(status_row)
        layout.addWidget(Separator())

        # 4×4 relay grid
        grid = QGridLayout()
        grid.setSpacing(8)
        for i in range(NUM_CHANNELS):
            btn = RelayButton(i, self.labels.get(i))
            btn.clicked.connect(lambda _, b=btn: self._toggle(b))
            self.buttons.append(btn)
            grid.addWidget(btn, i // 4, i % 4)
        layout.addLayout(grid)

        layout.addWidget(Separator())

        # All ON / All OFF
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        all_on = QPushButton("ALL ON")
        all_on.setFont(QFont("Sans", 12, QFont.Bold))
        all_on.setStyleSheet("""
            QPushButton {
                background-color: #1b5e20;
                color: #a5d6a7;
                border: 2px solid #66bb6a;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:pressed { background-color: #2e7d32; }
        """)
        all_on.clicked.connect(lambda: self._set_all(True))

        all_off = QPushButton("ALL OFF")
        all_off.setFont(QFont("Sans", 12, QFont.Bold))
        all_off.setStyleSheet("""
            QPushButton {
                background-color: #b71c1c;
                color: #ef9a9a;
                border: 2px solid #ef5350;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:pressed { background-color: #c62828; }
        """)
        all_off.clicked.connect(lambda: self._set_all(False))

        ctrl_row.addWidget(all_on)
        ctrl_row.addWidget(all_off)
        layout.addLayout(ctrl_row)

    def _toggle(self, btn: RelayButton):
        new_state = not btn.is_on
        if self.board.set_relay(btn.channel, new_state):
            btn.set_state(new_state)

    def _set_all(self, state):
        if self.board.set_all(state):
            for btn in self.buttons:
                btn.set_state(state)

    def poll(self):
        states = self.board.read_states()
        if states is not None:
            self.status_label.setText("CONNECTED")
            self.status_label.setStyleSheet("color: #66bb6a;")
            for i, btn in enumerate(self.buttons):
                btn.set_state(states[i])
        else:
            self.status_label.setText("DISCONNECTED")
            self.status_label.setStyleSheet("color: #ef5350;")
            self.board.connect()


# ── Main window ───────────────────────────────────────────────────────────────

class RelayControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relay Control — Dig 'Em Aggies")
        self.setStyleSheet("background-color: #1a1a1a;")
        self.resize(430, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title = QLabel("DIG 'EM AGGIES  —  RELAY CONTROL")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Sans", 16, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)
        layout.addWidget(Separator())

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2c2c2c;
                color: #9e9e9e;
                border: 1px solid #444444;
                padding: 8px 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border-bottom: 2px solid #42a5f5;
            }
        """)

        self.board_tabs: list[BoardTab] = []
        for cfg in RELAY_BOARDS:
            board = RelayBoard(cfg["ip"], cfg["port"])
            board.connect()
            tab = BoardTab(board, cfg["name"], cfg.get("labels", {}))
            self.board_tabs.append(tab)
            self.tabs.addTab(tab, cfg["name"])

        layout.addWidget(self.tabs)

        self.timer = QTimer()
        self.timer.timeout.connect(self._poll)
        self.timer.start(1000)
        self._poll()

    def _poll(self):
        for tab in self.board_tabs:
            tab.poll()


def main():
    app = QApplication(sys.argv)
    w = RelayControlPanel()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
