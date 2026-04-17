"""
IO List Tab  (NaBC 2026 Rules Section 8d)
Required by TBC inspectors at Mining Readiness Review.
Shows every sensor input and control output with:
  - Low Alarm / Low Warn / Actual / High Warn / High Alarm / Units
  - Live actual values colour-coded by threshold status
  - Relay channel outputs with current ON/OFF state
  - Export to CSV for printing/submission
"""

import csv
import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QAbstractItemView, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from config import IO_THRESHOLDS

SECTION_BG  = "#1a0000"
CARD_BG     = "#500000"
CARD_BORDER = "#7a1515"
TEXT_COLOR  = "#ffffff"
DIM_COLOR   = "#aaaaaa"

OK_COLOR    = QColor("#1a4a1a")
WARN_COLOR  = QColor("#3a2a00")
ALARM_COLOR = QColor("#3a0000")
NA_COLOR    = QColor("#1a1a1a")

OK_TEXT     = QColor("#4caf50")
WARN_TEXT   = QColor("#c8820a")
ALARM_TEXT  = QColor("#ff4444")
NA_TEXT     = QColor("#666666")


# (display_name, threshold_key, device, interface)
SENSOR_IO = [
    ("Cutterhead RPM",       "RPM",        "Teensy 1", "Optocoupler  Pin 2"),
    ("Flow Rate",            "Flow",       "Teensy 1", "Optocoupler  Pin 3"),
    ("Bore Depth",           "Depth",      "Teensy 1", "TF-Luna LiDAR  I2C"),
    ("Roll",                 "Roll",       "Teensy 1", "BNO085 IMU  I2C"),
    ("Pitch",                "Pitch",      "Teensy 1", "BNO085 IMU  I2C"),
    ("Yaw / Heading",        "Yaw",        "Teensy 1", "BNO085 IMU  I2C"),
    ("Relay 1 Voltage",      "Relay1_V",   "Teensy 2", "INA260 #1  I2C 0x40"),
    ("Relay 1 Current",      "Relay1_A",   "Teensy 2", "INA260 #1  I2C 0x40"),
    ("Relay 2 Voltage",      "Relay2_V",   "Teensy 2", "INA260 #2  I2C 0x41"),
    ("Relay 2 Current",      "Relay2_A",   "Teensy 2", "INA260 #2  I2C 0x41"),
    ("24V Rail Voltage",     "Rail24V_V",  "Teensy 2", "INA260 #3  I2C 0x44"),
    ("24V Rail Current",     "Rail24V_A",  "Teensy 2", "INA260 #3  I2C 0x44"),
    ("12V Rail Voltage",     "Rail12V_V",  "Teensy 2", "INA260 #4  I2C 0x45"),
    ("12V Rail Current",     "Rail12V_A",  "Teensy 2", "INA260 #4  I2C 0x45"),
    ("Enclosure Temp 1",     "Encl_Temp1", "Teensy 2", "DS18B20  1-Wire Pin 4"),
    ("Enclosure Temp 2",     "Encl_Temp2", "Teensy 2", "DS18B20  1-Wire Pin 4"),
]

# Control outputs (relay channels)
# (display_name, relay, ch, device, voltage)
RELAY_IO = [
    ("E-Brake 1  12V",          1, 1, "Relay 1", "12V"),
    ("E-Brake 1  GND",          1, 2, "Relay 1", "GND"),
    ("E-Brake 2  12V",          1, 3, "Relay 1", "12V"),
    ("E-Brake 2  GND",          1, 4, "Relay 1", "GND"),
    ("Injection Pump  120VAC",  1, 7, "Relay 1", "120VAC"),
    ("Injection Pump  120VAC",  1, 8, "Relay 1", "120VAC"),
    ("Signal Light  Green",     2, 1, "Relay 2", "24V"),
    ("Signal Light  Yellow",    2, 2, "Relay 2", "24V"),
    ("Signal Light  Red",       2, 3, "Relay 2", "24V"),
    ("Signal Buzzer",           2, 4, "Relay 2", "24V"),
    ("Signal Light  GND",       2, 5, "Relay 2", "GND"),
]

SENSOR_COLS  = ["Component / Sensor", "Device", "Interface",
                "Low Alarm", "Low Warn", "Actual", "High Warn", "High Alarm", "Units", "Status"]
RELAY_COLS   = ["Control Output", "Device", "Relay CH",
                "Voltage", "State", "Interlock"]


class IOListTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{SECTION_BG};")

        self._sensor_actuals = {}   # key → float
        self._relay_states   = {}   # (relay, ch) → bool

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        toolbar = QHBoxLayout()
        title = QLabel("IO List  —  NaBC 2026 Section 8d")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet(f"color:{TEXT_COLOR};")
        toolbar.addWidget(title)
        toolbar.addStretch()

        export_btn = QPushButton("⬇ Export CSV")
        export_btn.setFixedHeight(30)
        export_btn.setFont(QFont("Segoe UI", 9))
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color:{CARD_BG};
                color:{TEXT_COLOR};
                border:1px solid {CARD_BORDER};
                border-radius:4px;
                padding:2px 12px;
            }}
            QPushButton:hover {{ background-color:#6a0000; }}
        """)
        export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(export_btn)
        root.addLayout(toolbar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{CARD_BORDER};")
        root.addWidget(sep)

        sens_lbl = QLabel("Sensor Inputs")
        sens_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        sens_lbl.setStyleSheet(f"color:{DIM_COLOR};")
        root.addWidget(sens_lbl)

        self._sens_table = self._make_table(SENSOR_COLS)
        self._populate_sensors()
        root.addWidget(self._sens_table, stretch=3)

        ctrl_lbl = QLabel("Control Outputs  (Relay Channels)")
        ctrl_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ctrl_lbl.setStyleSheet(f"color:{DIM_COLOR};")
        root.addWidget(ctrl_lbl)

        self._relay_table = self._make_table(RELAY_COLS)
        self._populate_relays()
        root.addWidget(self._relay_table, stretch=2)


    def update_sensor(self, key: str, value: float):
        self._sensor_actuals[key] = value
        self._refresh_sensor_row(key, value)

    def update_relay(self, relay: int, ch: int, state: bool):
        self._relay_states[(relay, ch)] = state
        self._refresh_relay_row(relay, ch, state)


    def _make_table(self, columns):
        t = QTableWidget()
        t.setColumnCount(len(columns))
        t.setHorizontalHeaderLabels(columns)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setAlternatingRowColors(False)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        t.horizontalHeader().setStretchLastSection(True)
        t.setStyleSheet(f"""
            QTableWidget {{
                background-color: #1a0000;
                color: {TEXT_COLOR};
                gridline-color: #2a0000;
                border: 1px solid {CARD_BORDER};
                font-size: 10px;
            }}
            QHeaderView::section {{
                background-color: {CARD_BG};
                color: {TEXT_COLOR};
                border: 1px solid {CARD_BORDER};
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: #3a0000;
            }}
        """)
        return t

    def _cell(self, text, align=Qt.AlignCenter, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align | Qt.AlignVCenter)
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        return item

    def _populate_sensors(self):
        self._sens_table.setRowCount(len(SENSOR_IO))
        self._sens_row_map = {}   # key → row index (for updates)

        for row, (name, key, device, interface) in enumerate(SENSOR_IO):
            t = IO_THRESHOLDS.get(key, {})
            self._sens_row_map[key] = row

            self._sens_table.setItem(row, 0, self._cell(name, Qt.AlignLeft))
            self._sens_table.setItem(row, 1, self._cell(device))
            self._sens_table.setItem(row, 2, self._cell(interface, Qt.AlignLeft))
            self._sens_table.setItem(row, 3, self._cell(t.get("low_alarm",  "—")))
            self._sens_table.setItem(row, 4, self._cell(t.get("low_warn",   "—")))
            self._sens_table.setItem(row, 5, self._cell("—", bold=True))   # Actual
            self._sens_table.setItem(row, 6, self._cell(t.get("high_warn",  "—")))
            self._sens_table.setItem(row, 7, self._cell(t.get("high_alarm", "—")))
            self._sens_table.setItem(row, 8, self._cell(t.get("unit", "—")))
            self._sens_table.setItem(row, 9, self._cell("NO DATA"))

            for col in range(self._sens_table.columnCount()):
                item = self._sens_table.item(row, col)
                if item:
                    item.setBackground(NA_COLOR)
                    item.setForeground(NA_TEXT)

    def _populate_relays(self):
        self._relay_table.setRowCount(len(RELAY_IO))
        self._relay_row_map = {}

        for row, (name, relay, ch, device, voltage) in enumerate(RELAY_IO):
            self._relay_row_map[(relay, ch)] = row

            interlock = "PNOZ S5 (E-stop)" if relay == 1 else "None"
            self._relay_table.setItem(row, 0, self._cell(name, Qt.AlignLeft))
            self._relay_table.setItem(row, 1, self._cell(device))
            self._relay_table.setItem(row, 2, self._cell(f"CH{ch}"))
            self._relay_table.setItem(row, 3, self._cell(voltage))
            self._relay_table.setItem(row, 4, self._cell("OFF", bold=True))
            self._relay_table.setItem(row, 5, self._cell(interlock, Qt.AlignLeft))

            for col in range(self._relay_table.columnCount()):
                item = self._relay_table.item(row, col)
                if item:
                    item.setBackground(NA_COLOR)
                    item.setForeground(NA_TEXT)


    def _refresh_sensor_row(self, key: str, value: float):
        row = self._sens_row_map.get(key)
        if row is None:
            return
        t = IO_THRESHOLDS.get(key, {})

        # Determine status
        if t:
            if value <= t["low_alarm"] or value >= t["high_alarm"]:
                status, bg, fg = "ALARM", ALARM_COLOR, ALARM_TEXT
            elif value <= t["low_warn"] or value >= t["high_warn"]:
                status, bg, fg = "WARN",  WARN_COLOR,  WARN_TEXT
            else:
                status, bg, fg = "NORMAL", OK_COLOR,   OK_TEXT
        else:
            status, bg, fg = "NORMAL", OK_COLOR, OK_TEXT

        unit = t.get("unit", "")
        actual_item = self._cell(f"{value:.3f} {unit}".strip(), bold=True)
        actual_item.setBackground(bg)
        actual_item.setForeground(fg)
        self._sens_table.setItem(row, 5, actual_item)

        status_item = self._cell(status, bold=(status != "NORMAL"))
        status_item.setBackground(bg)
        status_item.setForeground(fg)
        self._sens_table.setItem(row, 9, status_item)

        # Colour whole row subtly
        for col in [0, 1, 2, 3, 4, 6, 7, 8]:
            item = self._sens_table.item(row, col)
            if item:
                item.setBackground(QColor("#1a1a1a") if status == "NORMAL"
                                   else QColor("#2a0000") if status == "ALARM"
                                   else QColor("#1a1200"))
                item.setForeground(QColor(TEXT_COLOR))

    def _refresh_relay_row(self, relay: int, ch: int, state: bool):
        row = self._relay_row_map.get((relay, ch))
        if row is None:
            return
        bg = QColor("#1a4a1a") if state else NA_COLOR
        fg = OK_TEXT           if state else NA_TEXT

        state_item = self._cell("ON" if state else "OFF", bold=True)
        state_item.setBackground(bg)
        state_item.setForeground(fg)
        self._relay_table.setItem(row, 4, state_item)

        for col in [0, 1, 2, 3, 5]:
            item = self._relay_table.item(row, col)
            if item:
                item.setBackground(bg)
                item.setForeground(fg)


    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export IO List",
            f"digem_io_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV files (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"DiGEM TBM — IO List  |  Exported {datetime.datetime.now()}"])
            w.writerow([])

            # Sensor inputs
            w.writerow(["SENSOR INPUTS"])
            w.writerow(SENSOR_COLS)
            for row in range(self._sens_table.rowCount()):
                w.writerow([
                    self._sens_table.item(row, col).text()
                    for col in range(self._sens_table.columnCount())
                ])

            w.writerow([])

            # Control outputs
            w.writerow(["CONTROL OUTPUTS"])
            w.writerow(RELAY_COLS)
            for row in range(self._relay_table.rowCount()):
                w.writerow([
                    self._relay_table.item(row, col).text()
                    for col in range(self._relay_table.columnCount())
                ])
