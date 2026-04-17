"""
Log Tab
-------
Timestamped event log for all system events:
  ALARM    — sensor threshold alarm breaches (red)
  WARN     — sensor threshold warnings (amber)
  STATE    — system state changes (blue)
  COMMS    — device connect/disconnect (purple)
  CONTROL  — relay channel changes (orange)
  INFO     — general events (white)

Filterable by category. Exportable to .txt file.
"""

import datetime
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

# ── Style constants ───────────────────────────────────────────────────────────
SECTION_BG  = "#1a0000"
CARD_BG     = "#500000"
CARD_BORDER = "#7a1515"
TEXT_COLOR  = "#ffffff"
DIM_COLOR   = "#aaaaaa"

# Category colours
CAT_COLORS = {
    "ALARM":   "#ff4444",
    "WARN":    "#c8820a",
    "STATE":   "#4a9eff",
    "COMMS":   "#cc88ff",
    "CONTROL": "#ff9944",
    "INFO":    "#cccccc",
}

CAT_BG = {
    "ALARM":   "#2a0000",
    "WARN":    "#1a1200",
    "STATE":   "#001a2a",
    "COMMS":   "#1a0028",
    "CONTROL": "#1a0e00",
    "INFO":    "#1a1a1a",
}

MAX_ENTRIES = 500   # drop oldest beyond this


# ── Single log entry widget ───────────────────────────────────────────────────
class LogEntry(QWidget):

    def __init__(self, timestamp: str, category: str, message: str, parent=None):
        super().__init__(parent)
        self.category  = category
        self.timestamp = timestamp
        self.message   = message

        color  = CAT_COLORS.get(category, TEXT_COLOR)
        bg     = CAT_BG.get(category, "#1a1a1a")

        self.setStyleSheet(
            f"background-color:{bg};"
            f"border-bottom:1px solid #2a0000;"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 4, 10, 4)
        row.setSpacing(10)

        ts_lbl = QLabel(timestamp)
        ts_lbl.setFont(QFont("Courier New", 9))
        ts_lbl.setFixedWidth(90)
        ts_lbl.setStyleSheet(f"color:{DIM_COLOR}; background:transparent;")
        row.addWidget(ts_lbl)

        cat_lbl = QLabel(f"[{category}]")
        cat_lbl.setFont(QFont("Courier New", 9, QFont.Bold))
        cat_lbl.setFixedWidth(72)
        cat_lbl.setStyleSheet(f"color:{color}; background:transparent;")
        row.addWidget(cat_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setFont(QFont("Segoe UI", 9))
        msg_lbl.setStyleSheet(f"color:{color}; background:transparent;")
        msg_lbl.setWordWrap(True)
        row.addWidget(msg_lbl, stretch=1)


# ── Filter toggle button ──────────────────────────────────────────────────────
class FilterBtn(QPushButton):

    def __init__(self, category: str, parent=None):
        super().__init__(category, parent)
        self._category = category
        self._active   = True
        self.setCheckable(True)
        self.setChecked(True)
        self.setFixedHeight(28)
        self.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._refresh()
        self.toggled.connect(lambda _: self._refresh())

    def _refresh(self):
        color = CAT_COLORS.get(self._category, TEXT_COLOR)
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CAT_BG.get(self._category, '#1a1a1a')};
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 4px;
                    padding: 2px 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a0000;
                    color: #555555;
                    border: 1px solid #333333;
                    border-radius: 4px;
                    padding: 2px 10px;
                }}
            """)


# ── Log Tab ───────────────────────────────────────────────────────────────────
class LogTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{SECTION_BG};")

        self._entries    = []   # list of LogEntry (newest last)
        self._auto_scroll = True

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        lbl = QLabel("Filter:")
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color:{DIM_COLOR};")
        toolbar.addWidget(lbl)

        self._filters = {}
        for cat in ["ALARM", "WARN", "STATE", "COMMS", "CONTROL", "INFO"]:
            btn = FilterBtn(cat)
            btn.toggled.connect(self._apply_filters)
            self._filters[cat] = btn
            toolbar.addWidget(btn)

        toolbar.addStretch()

        # Entry count
        self._count_lbl = QLabel("0 entries")
        self._count_lbl.setFont(QFont("Segoe UI", 9))
        self._count_lbl.setStyleSheet(f"color:{DIM_COLOR};")
        toolbar.addWidget(self._count_lbl)

        # Auto-scroll toggle
        self._autoscroll_btn = QPushButton("⬇ Auto-scroll: ON")
        self._autoscroll_btn.setCheckable(True)
        self._autoscroll_btn.setChecked(True)
        self._autoscroll_btn.setFixedHeight(28)
        self._autoscroll_btn.setFont(QFont("Segoe UI", 9))
        self._autoscroll_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a3a1a;
                color: #66cc66;
                border: 1px solid #448844;
                border-radius: 4px;
                padding: 2px 10px;
            }}
            QPushButton:!checked {{
                background-color: #1a0000;
                color: #666666;
                border: 1px solid #333333;
            }}
        """)
        self._autoscroll_btn.toggled.connect(self._on_autoscroll_toggle)
        toolbar.addWidget(self._autoscroll_btn)

        # Export button
        export_btn = QPushButton("⬇ Export")
        export_btn.setFixedHeight(28)
        export_btn.setFont(QFont("Segoe UI", 9))
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CARD_BG};
                color: {TEXT_COLOR};
                border: 1px solid {CARD_BORDER};
                border-radius: 4px;
                padding: 2px 10px;
            }}
            QPushButton:hover {{ background-color: #6a0000; }}
        """)
        export_btn.clicked.connect(self._export)
        toolbar.addWidget(export_btn)

        # Clear button
        clear_btn = QPushButton("✕ Clear")
        clear_btn.setFixedHeight(28)
        clear_btn.setFont(QFont("Segoe UI", 9))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CARD_BG};
                color: #ff8888;
                border: 1px solid #cc2222;
                border-radius: 4px;
                padding: 2px 10px;
            }}
            QPushButton:hover {{ background-color: #6a0000; }}
        """)
        clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(clear_btn)

        root.addLayout(toolbar)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{CARD_BORDER};")
        root.addWidget(sep)

        # ── Scroll area with log entries ──────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color:{SECTION_BG}; }}
            QScrollBar:vertical {{
                background: #1a0000;
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {CARD_BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
        """)

        self._container = QWidget()
        self._container.setStyleSheet(f"background-color:{SECTION_BG};")
        self._log_layout = QVBoxLayout(self._container)
        self._log_layout.setContentsMargins(0, 0, 0, 0)
        self._log_layout.setSpacing(0)
        self._log_layout.addStretch()

        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, stretch=1)

        # Seed with startup entry
        self.log("INFO", "Operator UI started")

    # ── Public API ────────────────────────────────────────────────────────────

    def log(self, category: str, message: str):
        """Add a new log entry. category = ALARM|WARN|STATE|COMMS|CONTROL|INFO"""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(ts, category.upper(), message)
        self._entries.append(entry)

        # Remove oldest if over limit
        if len(self._entries) > MAX_ENTRIES:
            oldest = self._entries.pop(0)
            self._log_layout.removeWidget(oldest)
            oldest.deleteLater()

        # Insert before the trailing stretch (last item)
        self._log_layout.insertWidget(self._log_layout.count() - 1, entry)

        # Apply current filter visibility
        cat = category.upper()
        entry.setVisible(self._filters.get(cat, FilterBtn(cat)).isChecked())

        self._count_lbl.setText(f"{len(self._entries)} entries")

        if self._auto_scroll:
            QTimer.singleShot(50, self._scroll_to_bottom)

    def clear(self):
        for entry in self._entries:
            self._log_layout.removeWidget(entry)
            entry.deleteLater()
        self._entries.clear()
        self._count_lbl.setText("0 entries")
        self.log("INFO", "Log cleared")

    # Convenience wrappers
    def log_state(self, new_state: str):
        self.log("STATE", f"System state → {new_state}")

    def log_alarm(self, sensor: str, value: float, label: str):
        self.log("ALARM", f"{sensor}: {value:.2f}  [{label}]")

    def log_warn(self, sensor: str, value: float, label: str):
        self.log("WARN", f"{sensor}: {value:.2f}  [{label}]")

    def log_alarm_clear(self, sensor: str):
        self.log("INFO", f"{sensor}: alarm/warn cleared — back to normal")

    def log_connection(self, device: str, connected: bool, stale: bool = False):
        if stale:
            self.log("COMMS", f"{device}: data stale (no update for 10 s)")
        elif connected:
            self.log("COMMS", f"{device}: connected")
        else:
            self.log("COMMS", f"{device}: disconnected")

    def log_relay(self, relay: int, ch: int, label: str, on: bool):
        self.log("CONTROL", f"Relay {relay} CH{ch} ({label}): {'ON' if on else 'OFF'}")

    def log_estop(self):
        self.log("ALARM", "ALL OUTPUTS OFF — software relay zero command sent")

    def log_reset(self):
        self.log("STATE", "Software reset — system returned to IDLE")

    def log_mining(self, active: bool):
        self.log("INFO", f"Mining {'STARTED' if active else 'STOPPED'} — MQTT telemetry {'publishing' if active else 'paused'}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _apply_filters(self):
        for entry in self._entries:
            visible = self._filters.get(entry.category, FilterBtn(entry.category)).isChecked()
            entry.setVisible(visible)

    def _on_autoscroll_toggle(self, checked: bool):
        self._auto_scroll = checked
        self._autoscroll_btn.setText(f"⬇ Auto-scroll: {'ON' if checked else 'OFF'}")
        if checked:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Log", f"digem_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt)"
        )
        if not path:
            return
        with open(path, "w") as f:
            f.write(f"DiGEM TBM Operator Log — exported {datetime.datetime.now()}\n")
            f.write("=" * 60 + "\n")
            for e in self._entries:
                f.write(f"{e.timestamp}  [{e.category:<7}]  {e.message}\n")
        self.log("INFO", f"Log exported to {os.path.basename(path)}")
