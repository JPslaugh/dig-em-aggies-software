#!/usr/bin/env python3
#
# System Monitor for digem-pi5 (Raspberry Pi 5)
#
# Hardware:
#   - Geekworm X1202 UPS HAT (4x 18650 lithium cells wired in parallel)
#   - MAX17040G+ fuel gauge IC on I2C bus 1, address 0x36
#   - Cells are parallel so there is only one voltage reading for the whole pack
#   - No current/amperage sensor on the X1202 — only voltage and state of charge
#   - Pi 5 ethernet interface may be "eth0" or "end0" depending on OS version
#
# Data available from hardware:
#   - CPU temperature: via `vcgencmd measure_temp` (Pi-specific command)
#   - Battery cell voltage: MAX17040 register 0x02 (VCELL), returns float in volts
#   - Battery state of charge: MAX17040 register 0x04 (SOC), returns float 0-100%
#   - Power source detection: voltage > 4.15V means outlet power (charging),
#     below means running on battery. This is a heuristic, not a dedicated flag.
#   - Time remaining estimate: rough linear estimate assuming ~2.5h at full charge
#     under typical Pi 5 load. NOT accurate — no current sensing available.
#
# I2C notes:
#   - The X1202 connects to GPIO pins 3 (SDA) and 5 (SCL) via pogo pins on the
#     underside of the HAT. These pins must be clean for reliable contact.
#   - MAX17040 uses big-endian byte order, smbus2 reads little-endian,
#     so all register reads need byte-swapping.
#   - If I2C fails (bus or device not found), the app gracefully shows "No UPS"
#     and retries on each update cycle.
#
# Dependencies: python3-pyqt5, python3-smbus2
# Run on Pi: WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000
#            QT_QPA_PLATFORM=wayland python3 system_monitor.py
#

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

    # MAX17040 I2C address and register map
    FUEL_GAUGE_ADDR = 0x36
    REG_VCELL = 0x02  # Battery voltage register (big-endian, 12-bit, units of 1.25mV)
    REG_SOC = 0x04    # State of charge register (big-endian, upper byte = whole %, lower = fraction)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dig 'Em Aggies - System Monitor")
        self.setStyleSheet("background-color: #500000;")
        self.resize(520, 520)

        self.bus = None
        self.addr = self.FUEL_GAUGE_ADDR
        self.prev_capacity = None
        self.try_connect_i2c()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

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

        self.big_charge = QLabel("--%")
        self.big_charge.setFont(QFont("Sans", 48, QFont.Bold))
        self.big_charge.setStyleSheet("color: #00ff00; border: none;")
        self.big_charge.setAlignment(Qt.AlignCenter)

        bat_card.setLayout(bat_grid)
        main_layout.addWidget(bat_card)
        main_layout.addWidget(self.big_charge)

        self.setLayout(main_layout)

        # Poll every 2 seconds — safe rate for MAX17040 (updates internally every ~500ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(2000)
        self.update_all()
        self.update_ip()

    def try_connect_i2c(self):
        """Connect to I2C bus 1. The X1202 HAT uses bus 1 on the Pi 5 GPIO header."""
        try:
            self.bus = smbus2.SMBus(1)
        except:
            self.bus = None

    def update_ip(self):
        """Get the IPv4 address of the ethernet interface.
        Pi 5 may name it 'eth0' or 'end0' depending on OS/firmware version."""
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
        """Read CPU temperature using vcgencmd (Raspberry Pi specific).
        Returns temperature as a string like '52.1' (degrees Celsius), or None."""
        try:
            result = subprocess.run(["vcgencmd", "measure_temp"],
                                    capture_output=True, text=True)
            return result.stdout.strip().replace("temp=", "").replace("'C", "")
        except:
            return None

    def get_voltage(self):
        """Read battery pack voltage from MAX17040 VCELL register (0x02).
        The raw value is a 12-bit number in units of 1.25mV, packed big-endian.
        smbus2 reads as little-endian so we byte-swap before converting.
        Returns voltage as float (e.g. 4.01), or None if I2C read fails."""
        try:
            read = self.bus.read_word_data(self.addr, self.REG_VCELL)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped * 1.25 / 1000 / 16
        except:
            return None

    def get_capacity(self):
        """Read battery state of charge from MAX17040 SOC register (0x04).
        Upper byte is whole percentage, lower byte is 1/256th fraction.
        Returns SOC as float 0-100 (e.g. 83.5), or None if I2C read fails.
        Note: under load while charging, this typically maxes out around 84%
        because the cell voltage can't reach true 4.2V while powering the Pi."""
        try:
            read = self.bus.read_word_data(self.addr, self.REG_SOC)
            swapped = struct.unpack("<H", struct.pack(">H", read))[0]
            return swapped / 256
        except:
            return None

    def update_all(self):
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

        if self.bus is None:
            self.try_connect_i2c()

        voltage = self.get_voltage()
        capacity = self.get_capacity()

        if voltage is not None:
            self.voltage_label.setText(f"{voltage:.2f}V")

            # Voltage > 4.15V indicates outlet power is connected and cells are charging.
            # Below 4.15V means running on battery only. This threshold is a heuristic —
            # there is no dedicated "charging" pin or register on the MAX17040.
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

            # Time remaining is a rough linear estimate: assumes ~2.5 hours at 100%
            # under typical Pi 5 load (~3-5W). This is NOT accurate without a current
            # sensor. For better estimates, add an INA219 current sensor or track
            # SOC drop rate over time.
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
