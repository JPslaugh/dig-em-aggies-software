"""
Controls Tab  (password-protected — enforced by MainWindow)
-------------------------------------------------------------
Manual relay channel control for Relay 1 and Relay 2.
Modbus write stubs are marked TODO — wired in when comms layer lands.

Relay 1  192.168.100.10  — harmful devices (PNOZ S5 cuts 24V on physical E-stop)
  CH1  E-brake valve 1   12V
  CH2  E-brake valve 1   GND
  CH3  E-brake valve 2   12V
  CH4  E-brake valve 2   GND
  CH5  (unassigned)
  CH6  (unassigned)
  CH7  Liquid injection pump  120VAC
  CH8  Liquid injection pump  120VAC
  CH9–16  (unassigned)

Relay 2  192.168.100.11  — non-harmful devices (stays live on E-stop)
  CH1  Signal light Green   24V
  CH2  Signal light Yellow  24V
  CH3  Signal light Red     24V
  CH4  Signal light Buzzer  24V
  CH5  Signal light GND
  CH6–16  (unassigned)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from config import State

# ── Style constants ───────────────────────────────────────────────────────────
CARD_BG     = "#500000"
CARD_BORDER = "#7a1515"
SECTION_BG  = "#1a0000"
TEXT_COLOR  = "#ffffff"
DIM_COLOR   = "#aaaaaa"

# Channel definitions: (label, note, is_harmful, is_120vac)
RELAY1_CHANNELS = {
    1:  ("E-Brake 1",        "12V",    True,  False),
    2:  ("E-Brake 1 GND",    "",       True,  False),
    3:  ("E-Brake 2",        "12V",    True,  False),
    4:  ("E-Brake 2 GND",    "",       True,  False),
    5:  ("Unassigned",       "",       False, False),
    6:  ("Unassigned",       "",       False, False),
    7:  ("Injection Pump",   "120VAC", True,  True),
    8:  ("Injection Pump",   "120VAC", True,  True),
    9:  ("Unassigned",       "",       False, False),
    10: ("Unassigned",       "",       False, False),
    11: ("Unassigned",       "",       False, False),
    12: ("Unassigned",       "",       False, False),
    13: ("Unassigned",       "",       False, False),
    14: ("Unassigned",       "",       False, False),
    15: ("Unassigned",       "",       False, False),
    16: ("Unassigned",       "",       False, False),
}

RELAY2_CHANNELS = {
    1:  ("Signal: Green",    "24V",    False, False),
    2:  ("Signal: Yellow",   "24V",    False, False),
    3:  ("Signal: Red",      "24V",    False, False),
    4:  ("Signal: Buzzer",   "24V",    False, False),
    5:  ("Signal: GND",      "",       False, False),
    6:  ("Unassigned",       "",       False, False),
    7:  ("Unassigned",       "",       False, False),
    8:  ("Unassigned",       "",       False, False),
    9:  ("Unassigned",       "",       False, False),
    10: ("Unassigned",       "",       False, False),
    11: ("Unassigned",       "",       False, False),
    12: ("Unassigned",       "",       False, False),
    13: ("Unassigned",       "",       False, False),
    14: ("Unassigned",       "",       False, False),
    15: ("Unassigned",       "",       False, False),
    16: ("Unassigned",       "",       False, False),
}


# ── Channel button ────────────────────────────────────────────────────────────
class ChannelButton(QWidget):
    """Toggle button for a single relay channel."""

    toggled = pyqtSignal(int, bool)   # (channel_number, new_state)

    def __init__(self, relay: int, ch: int, label: str, note: str,
                 is_harmful: bool, is_120vac: bool, parent=None):
        super().__init__(parent)
        self._relay    = relay
        self._ch       = ch
        self._on       = False
        self._harmful  = is_harmful
        self._vac      = is_120vac
        self._locked   = False   # True when E-stopped (Relay 1 only)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        # Channel number badge
        ch_lbl = QLabel(f"CH{ch}")
        ch_lbl.setFont(QFont("Segoe UI", 8))
        ch_lbl.setAlignment(Qt.AlignCenter)
        ch_lbl.setStyleSheet(f"color:{DIM_COLOR};")
        outer.addWidget(ch_lbl)

        # Main toggle button
        self._btn = QPushButton("OFF")
        self._btn.setCheckable(True)
        self._btn.setFixedHeight(52)
        self._btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn.clicked.connect(self._on_click)
        outer.addWidget(self._btn)

        # Label + note
        name_lbl = QLabel(label)
        name_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet(f"color:{TEXT_COLOR};")
        outer.addWidget(name_lbl)

        if note:
            note_lbl = QLabel(note)
            note_lbl.setFont(QFont("Segoe UI", 7))
            note_lbl.setAlignment(Qt.AlignCenter)
            note_lbl.setStyleSheet(
                f"color:#ff8888;" if is_120vac else f"color:{DIM_COLOR};"
            )
            outer.addWidget(note_lbl)

        self._refresh_style()

    def set_state(self, on: bool):
        self._on = on
        self._btn.setChecked(on)
        self._refresh_style()

    def set_locked(self, locked: bool):
        """Lock channel (e.g. Relay 1 when E-stopped — hardware already cut it)."""
        self._locked = locked
        self._btn.setEnabled(not locked)
        self._refresh_style()

    def _on_click(self):
        self._on = self._btn.isChecked()
        self._refresh_style()
        self.toggled.emit(self._ch, self._on)
        # TODO: Modbus write — relay self._relay, coil self._ch - 1, value self._on

    def _refresh_style(self):
        if self._locked:
            self._btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a1a;
                    color: #555555;
                    border: 2px solid #333333;
                    border-radius: 6px;
                }
            """)
            self._btn.setText("LOCKED")
            return

        if self._on:
            if self._vac:
                # 120VAC — bright orange when on
                self._btn.setStyleSheet("""
                    QPushButton {
                        background-color: #7a3a00;
                        color: #ffcc44;
                        border: 2px solid #ff8800;
                        border-radius: 6px;
                    }
                    QPushButton:hover { background-color: #9a4a00; }
                    QPushButton:pressed { background-color: #5a2a00; }
                """)
            elif self._harmful:
                self._btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3a1a00;
                        color: #ff9944;
                        border: 2px solid #cc5500;
                        border-radius: 6px;
                    }
                    QPushButton:hover { background-color: #4a2a00; }
                    QPushButton:pressed { background-color: #2a1000; }
                """)
            else:
                self._btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a4a1a;
                        color: #66ff66;
                        border: 2px solid #44aa44;
                        border-radius: 6px;
                    }
                    QPushButton:hover { background-color: #226622; }
                    QPushButton:pressed { background-color: #113311; }
                """)
            self._btn.setText("ON")
        else:
            self._btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a0000;
                    color: #888888;
                    border: 2px solid #4a1515;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #3a0000; }
                QPushButton:pressed { background-color: #1a0000; }
                QPushButton:disabled {
                    background-color: #1a1a1a;
                    color: #555555;
                    border: 2px solid #333333;
                }
            """)
            self._btn.setText("OFF")


# ── Relay panel (one per relay board) ────────────────────────────────────────
class RelayPanel(QWidget):

    channel_toggled = pyqtSignal(int, int, bool)   # (relay, ch, state)

    def __init__(self, relay: int, label: str, ip: str,
                 channels: dict, parent=None):
        super().__init__(parent)
        self._relay = relay
        self._ch_widgets = {}

        self.setStyleSheet(
            f"background-color:{CARD_BG};"
            f"border:1px solid {CARD_BORDER};"
            f"border-radius:8px;"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        title = QLabel(f"Relay {relay}  —  {label}")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet(f"color:{TEXT_COLOR}; background:transparent; border:none;")
        hdr.addWidget(title)
        hdr.addStretch()
        ip_lbl = QLabel(ip)
        ip_lbl.setFont(QFont("Segoe UI", 9))
        ip_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent; border:none;")
        hdr.addWidget(ip_lbl)
        lay.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{CARD_BORDER};")
        lay.addWidget(sep)

        # 4-column grid of channel buttons
        grid = QGridLayout()
        grid.setSpacing(8)
        for idx, (ch, (lbl, note, harmful, vac)) in enumerate(channels.items()):
            btn = ChannelButton(relay, ch, lbl, note, harmful, vac)
            btn.toggled.connect(lambda ch=ch, b=btn: self._on_toggle(ch, b._on))
            self._ch_widgets[ch] = btn
            grid.addWidget(btn, idx // 4, idx % 4)
        lay.addLayout(grid)

    def _on_toggle(self, ch: int, state: bool):
        self.channel_toggled.emit(self._relay, ch, state)

    def set_channel(self, ch: int, on: bool):
        if ch in self._ch_widgets:
            self._ch_widgets[ch].set_state(on)

    def set_all_off(self):
        for w in self._ch_widgets.values():
            w.set_state(False)

    def set_relay1_locked(self, locked: bool):
        """Lock all Relay 1 channels when E-stopped (hardware already cut)."""
        for w in self._ch_widgets.values():
            w.set_locked(locked)


# ── Controls Tab ──────────────────────────────────────────────────────────────
class ControlsTab(QWidget):

    channel_toggled = pyqtSignal(int, int, bool)   # (relay, ch, state)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{SECTION_BG};")
        self._estopped = True

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Warning banner ────────────────────────────────────────────────────
        self._banner = QLabel(
            "⚠  MANUAL CONTROL MODE  —  Direct relay channel override active.\n"
            "Relay 1 channels are physically cut by the PNOZ S5 while E-stopped. "
            "Relay 2 stays live at all times."
        )
        self._banner.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._banner.setAlignment(Qt.AlignCenter)
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet("""
            QLabel {
                background-color: #3a1a00;
                color: #ffcc44;
                border: 2px solid #cc6600;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        root.addWidget(self._banner)

        # ── E-stop notice (shown when relay 1 is locked) ──────────────────────
        self._estop_notice = QLabel(
            "🔒  System is E-STOPPED — Relay 1 channels are locked (hardware power cut). "
            "Reset the physical E-stop and press RESET before operating Relay 1."
        )
        self._estop_notice.setFont(QFont("Segoe UI", 10))
        self._estop_notice.setAlignment(Qt.AlignCenter)
        self._estop_notice.setWordWrap(True)
        self._estop_notice.setStyleSheet("""
            QLabel {
                background-color: #2a0000;
                color: #ff6666;
                border: 2px solid #cc2222;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        root.addWidget(self._estop_notice)

        # ── Relay panels ──────────────────────────────────────────────────────
        panels_row = QHBoxLayout()
        panels_row.setSpacing(10)

        self.relay1_panel = RelayPanel(
            1, "Harmful Devices (PNOZ S5 protected)",
            "192.168.100.10", RELAY1_CHANNELS
        )
        self.relay1_panel.channel_toggled.connect(self.channel_toggled)

        self.relay2_panel = RelayPanel(
            2, "Non-Harmful Devices",
            "192.168.100.11", RELAY2_CHANNELS
        )
        self.relay2_panel.channel_toggled.connect(self.channel_toggled)

        panels_row.addWidget(self.relay1_panel)
        panels_row.addWidget(self.relay2_panel)
        root.addLayout(panels_row, stretch=1)

        # Apply initial E-stopped state
        self._apply_estop(True)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_system_state(self, state: str):
        estopped = (state == State.ESTOPPED)
        if estopped != self._estopped:
            self._estopped = estopped
            self._apply_estop(estopped)

    def set_channel(self, relay: int, ch: int, on: bool):
        """Reflect a Modbus read back into the UI."""
        if relay == 1:
            self.relay1_panel.set_channel(ch, on)
        elif relay == 2:
            self.relay2_panel.set_channel(ch, on)

    def all_outputs_off(self):
        """Called by the ALL OUTPUTS OFF button — zeroes UI state."""
        self.relay1_panel.set_all_off()
        self.relay2_panel.set_all_off()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _apply_estop(self, estopped: bool):
        self._estop_notice.setVisible(estopped)
        self.relay1_panel.set_relay1_locked(estopped)
        if estopped:
            self.relay1_panel.set_all_off()
