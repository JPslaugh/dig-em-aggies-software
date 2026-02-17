#!/usr/bin/env python3
import sys
import os
import struct
import subprocess
import socket
import smbus2
from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget,
                             QHBoxLayout, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor


class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("background-color: #803030; max-height: 2px;")


class InfoCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #3a0000;
                border: 1px solid #803030;
                border-radius: 8px;
                padding: 8px;
            }
        """)


class SystemMonitor(QWidget):
    PASSWORD = "digem2026"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dig 'Em Aggies - System Monitor")
        self.setStyleSheet("background-color: #500000;")
        self.resize(520, 520)

        self.bus = None
        self.addr = 0x36
        self.prev_capacity = None
        self.try_connect_i2c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # ── Title ──
        self.title = QLabel("DIG 'EM AGGIES")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Sans", 22, QFont.Bold))
        self.title.setStyleSheet("color: white; letter-spacing: 2px;")

        subtitle = QLabel("SYSTEM MONITOR")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Sans", 11))
        subtitle.setStyleSheet("color: #cc9999;")

        main_layout.addWidget(self.title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(Separator())

        # ── Network Info Card ──
        net_card = InfoCard()
        net_grid = QGridLayout()
        net_grid.setSpacing(4)

        net_header = QLabel("NETWORK")
        net_header.setFont(QFont("Sans", 10, QFont.Bold))
        net_header.setStyleSheet("color: #cc9999; border: none;")
        net_grid.addWidget(net_header, 0, 0, 1, 2)

        hostname = socket.gethostname()
        self.hostname_val = QLabel(hostname)
        self.ip_val = QLabel("---.---.---.---")
        self.pass_val = QLabel(self.PASSWORD)

        for row, (key, val_widget) in enumerate([
            ("Hostname", self.hostname_val),
            ("Ethernet IP", self.ip_val),
            ("Password", self.pass_val),
        ], start=1):
            lbl = QLabel(key)
            lbl.setFont(QFont("Sans", 13))
            lbl.setStyleSheet("color: #cc9999; border: none;")
            val_widget.setFont(QFont("Sans", 13, QFont.Bold))
            val_widget.setStyleSheet("color: white; border: none;")
            val_widget.setAlignment(Qt.AlignRight)
            net_grid.addWidget(lbl, row, 0)
            net_grid.addWidget(val_widget, row, 1)

        net_card.setLayout(net_grid)
        main_layout.addWidget(net_card)

        # ── CPU Temperature ──
        cpu_card = InfoCard()
        cpu_layout = QHBoxLayout()

        cpu_header = QLabel("CPU TEMP")
        cpu_header.setFont(QFont("Sans", 10, QFont.Bold))
        cpu_header.setStyleSheet("color: #cc9999; border: none;")

        self.temp_label = QLabel("--.-\u00b0C")
        self.temp_label.setFont(QFont("Sans", 32, QFont.Bold))
        self.temp_label.setStyleSheet("color: white; border: none;")
        self.temp_label.setAlignment(Qt.AlignRight)

        cpu_layout.addWidget(cpu_header)
        cpu_layout.addStretch()
        cpu_layout.addWidget(self.temp_label)
        cpu_card.setLayout(cpu_layout)
        main_layout.addWidget(cpu_card)

        # ── Power & Battery Card ──
        bat_card = InfoCard()
        bat_grid = QGridLayout()
        bat_grid.setSpacing(4)

        bat_header = QLabel("POWER")
        bat_header.setFont(QFont("Sans", 10, QFont.Bold))
        bat_header.setStyleSheet("color: #cc9999; border: none;")
        bat_grid.addWidget(bat_header, 0, 0, 1, 2)

        self.power_label = QLabel("---")
        self.voltage_label = QLabel("-.-V")
        self.capacity_label = QLabel("--%")
        self.time_label = QLabel("")

        for row, (key, val_widget) in enumerate([
            ("Source", self.power_label),
            ("Voltage", self.voltage_label),
            ("Charge", self.capacity_label),
            ("Remaining", self.time_label),
        ], start=1):
            lbl = QLabel(key)
            lbl.setFont(QFont("Sans", 13))
            lbl.setStyleSheet("color: #cc9999; border: none;")
            val_widget.setFont(QFont("Sans", 13, QFont.Bold))
            val_widget.setStyleSheet("color: white; border: none;")
            val_widget.setAlignment(Qt.AlignRight)
            bat_grid.addWidget(lbl, row, 0)
            bat_grid.addWidget(val_widget, row, 1)

        # Big charge percentage
        self.big_charge = QLabel("--%")
        self.big_charge.setFont(QFont("Sans", 48, QFont.Bold))
        self.big_charge.setStyleSheet("color: #00ff00; border: none;")
        self.big_charge.setAlignment(Qt.AlignCenter)

        bat_card.setLayout(bat_grid)
        main_layout.addWidget(bat_card)
        main_layout.addWidget(self.big_charge)

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(2000)
        self.update_all()
        self.update_ip()

    def try_connect_i2c(self):
        try:
            self.bus = smbus2.SMBus(1)
        except:
            self.bus = None

    def update_ip(self):
        try:
            result = subprocess.run(
                ["ip", "-4", "-o", "addr", "show", "dev", "eth0"],
                capture_output=True, text=True)
            line = result.stdout.strip()
            if line:
                ip = line.split()[3].split("/")[0]
                self.ip_val.setText(ip)
                return
        except:
            pass
        # fallback: try end0 (Pi 5 naming)
        try:
            result = subprocess.run(
                ["ip", "-4", "-o", "addr", "show", "dev", "end0"],
                capture_output=True, text=True)
            line = result.stdout.strip()
            if line:
                ip = line.split()[3].split("/")[0]
                self.ip_val.setText(ip)
                return
        except:
            pass
        self.ip_val.setText("No Ethernet")

    def get_temp(self):
        try:
            result = subprocess.run(["vcgencmd", "measure_temp"],
                                    capture_output=True, text=True)
            return result.stdout.strip().replace("temp=", "").replace("'C", "")
        except:
            return None

    def get_voltage(self):
        try:
            read = self.bus.read_word_data(self.addr, 2)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped * 1.25 / 1000 / 16
        except:
            return None

    def get_capacity(self):
        try:
            read = self.bus.read_word_data(self.addr, 4)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped / 256
        except:
            return None

    def update_all(self):
        # Temperature
        temp = self.get_temp()
        if temp:
            self.temp_label.setText(f"{temp}\u00b0C")
            t = float(temp)
            if t > 70:
                self.temp_label.setStyleSheet("color: red; border: none;")
            elif t > 60:
                self.temp_label.setStyleSheet("color: orange; border: none;")
            else:
                self.temp_label.setStyleSheet("color: white; border: none;")

        # Battery
        if self.bus is None:
            self.try_connect_i2c()

        voltage = self.get_voltage()
        capacity = self.get_capacity()

        if voltage is not None:
            self.voltage_label.setText(f"{voltage:.2f}V")

            if voltage > 4.15:
                self.power_label.setText("\u26a1 Outlet (Charging)")
                self.power_label.setStyleSheet("color: #00ff00; border: none;")
            else:
                self.power_label.setText("\U0001f50b Battery")
                self.power_label.setStyleSheet("color: orange; border: none;")
        else:
            self.voltage_label.setText("No UPS")
            self.voltage_label.setStyleSheet("color: gray; border: none;")
            self.power_label.setText("Unknown")
            self.power_label.setStyleSheet("color: gray; border: none;")

        if capacity is not None:
            pct = f"{capacity:.0f}%"
            self.capacity_label.setText(pct)
            self.big_charge.setText(pct)

            if capacity < 20:
                color = "red"
            elif capacity < 50:
                color = "orange"
            else:
                color = "#00ff00"
            self.capacity_label.setStyleSheet(f"color: {color}; border: none;")
            self.big_charge.setStyleSheet(f"color: {color}; border: none;")

            if self.prev_capacity is not None and voltage is not None and voltage < 4.15:
                hours_left = (capacity / 100) * 2.5
                if hours_left > 0:
                    h = int(hours_left)
                    m = int((hours_left - h) * 60)
                    self.time_label.setText(f"~{h}h {m}m")
                else:
                    self.time_label.setText("--")
            elif voltage is not None and voltage >= 4.15:
                self.time_label.setText("Charging")
                self.time_label.setStyleSheet("color: #00ff00; border: none;")

            self.prev_capacity = capacity
        else:
            self.capacity_label.setText("--")
            self.capacity_label.setStyleSheet("color: gray; border: none;")
            self.big_charge.setText("--%")
            self.big_charge.setStyleSheet("color: gray; border: none;")
            self.time_label.setText("")


app = QApplication(sys.argv)
w = SystemMonitor()
w.show()
sys.exit(app.exec_())
