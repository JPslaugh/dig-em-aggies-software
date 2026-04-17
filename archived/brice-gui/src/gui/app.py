import json
import os
import sys
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets


TELEMETRY_PATH = os.environ.get("ROV_TELEMETRY_PATH", "./telemetry.json")
POLL_INTERVAL_MS = 200


class TelemetryReader(QtCore.QObject):
    telemetryUpdated = QtCore.Signal(dict)
    telemetryMissing = QtCore.Signal()

    def __init__(self, path: str, poll_interval_ms: int = POLL_INTERVAL_MS):
        super().__init__()
        self._path = path
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(poll_interval_ms)
        self._timer.timeout.connect(self._poll)
        self._last_mtime = 0.0

    def start(self) -> None:
        self._timer.start()
        self._poll()

    def _poll(self) -> None:
        if not os.path.exists(self._path):
            self.telemetryMissing.emit()
            return

        try:
            mtime = os.path.getmtime(self._path)
            if mtime == self._last_mtime:
                return
            self._last_mtime = mtime

            with open(self._path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.telemetryUpdated.emit(payload)
        except Exception:
            self.telemetryMissing.emit()


class StatusCard(QtWidgets.QFrame):
    def __init__(self, title: str, value: str = "--") -> None:
        super().__init__()
        self.setObjectName("statusCard")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self._title = QtWidgets.QLabel(title)
        self._title.setObjectName("cardTitle")
        self._value = QtWidgets.QLabel(value)
        self._value.setObjectName("cardValue")

        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addStretch(1)

    def setValue(self, value: str) -> None:
        self._value.setText(value)


def _section_title(text: str) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def _build_table(headers: list[str]) -> QtWidgets.QTableWidget:
    table = QtWidgets.QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(
        QtWidgets.QHeaderView.Stretch
    )
    table.verticalHeader().setVisible(False)
    table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
    table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setObjectName("dataTable")
    return table


def _update_table(table: QtWidgets.QTableWidget, rows: list[list[str]]) -> None:
    table.setRowCount(len(rows))
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            item = QtWidgets.QTableWidgetItem(value)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setItem(row_idx, col_idx, item)


def _placeholder_pixmap(text: str, width: int, height: int) -> QtGui.QPixmap:
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtGui.QColor("#111827"))
    painter = QtGui.QPainter(pixmap)
    painter.setPen(QtGui.QColor("#94A3B8"))
    painter.setFont(QtGui.QFont("Arial", 14))
    painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, text)
    painter.end()
    return pixmap


class ControlWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NABC ROV Control")
        self.resize(1300, 820)
        self._data_window = None

        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        root_layout = QtWidgets.QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(16)

        self.status_label = QtWidgets.QLabel("Waiting for telemetry")
        self.status_label.setObjectName("headerStatus")
        self.timestamp_label = QtWidgets.QLabel("--")
        self.timestamp_label.setObjectName("headerTimestamp")

        header_layout.addWidget(self.status_label)
        header_layout.addStretch(1)
        header_layout.addWidget(QtWidgets.QLabel("Last update:"))
        header_layout.addWidget(self.timestamp_label)
        root_layout.addLayout(header_layout)

        self.output_log = QtWidgets.QTextEdit()
        self.output_log.setObjectName("outputLog")
        self.output_log.setReadOnly(True)
        self.output_log.setPlaceholderText("Output log...")
        self.warning_log = QtWidgets.QTextEdit()
        self.warning_log.setObjectName("warningLog")
        self.warning_log.setReadOnly(True)
        self.warning_log.setPlaceholderText("Warning log...")

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(16)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setSpacing(12)
        left_layout.addWidget(self._runtime_panel())
        left_layout.addWidget(self._motor_panel())
        left_layout.addWidget(self._system_toggle_panel())
        left_layout.addStretch(1)

        middle_layout = QtWidgets.QVBoxLayout()
        middle_layout.setSpacing(12)
        middle_layout.addWidget(self._clamps_panel())
        middle_layout.addStretch(1)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setSpacing(12)
        right_layout.addWidget(self._connection_panel())
        right_layout.addWidget(self._stop_panel())
        right_layout.addWidget(self._launch_panel())
        right_layout.addStretch(1)

        content_layout.addLayout(left_layout, 3)
        content_layout.addLayout(middle_layout, 4)
        content_layout.addLayout(right_layout, 3)

        root_layout.addLayout(content_layout, 1)

        logs_layout = QtWidgets.QHBoxLayout()
        logs_layout.setSpacing(16)
        logs_layout.addWidget(self._wrap_section("Output Log", self.output_log))
        logs_layout.addWidget(self._wrap_section("Warning Log", self.warning_log))
        root_layout.addLayout(logs_layout)

    def set_data_window(self, window: "DataWindow") -> None:
        self._data_window = window

    def _wrap_section(self, title: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox()
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(_section_title(title))
        layout.addWidget(widget)
        return box

    def _runtime_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Runtime")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        self.runtime_label = QtWidgets.QLabel("00:00:00")
        self.runtime_label.setObjectName("runtimeLabel")
        start_button = QtWidgets.QPushButton("Start Program")
        stop_button = QtWidgets.QPushButton("Stop Program")
        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(start_button)
        button_row.addWidget(stop_button)
        layout.addWidget(self.runtime_label)
        layout.addLayout(button_row)
        return box

    def _motor_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Motor Controller")
        box.setObjectName("panelBox")
        layout = QtWidgets.QGridLayout(box)
        layout.addWidget(QtWidgets.QLabel("Speed (RPM)"), 0, 0)
        self.motor_speed_input = QtWidgets.QLineEdit()
        self.motor_speed_input.setPlaceholderText("Enter RPM")
        self.motor_speed_set = QtWidgets.QLabel("--")
        self.motor_speed_set.setObjectName("valueLabel")
        set_button = QtWidgets.QPushButton("Set")
        layout.addWidget(self.motor_speed_input, 0, 1)
        layout.addWidget(set_button, 0, 2)
        layout.addWidget(QtWidgets.QLabel("Last set"), 1, 0)
        layout.addWidget(self.motor_speed_set, 1, 1, 1, 2)
        return box

    def _system_toggle_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("System Toggles")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        self.toggle_drive = QtWidgets.QCheckBox("Drive System")
        self.toggle_hydraulics = QtWidgets.QCheckBox("Hydraulics")
        self.toggle_telemetry = QtWidgets.QCheckBox("Telemetry")
        layout.addWidget(self.toggle_drive)
        layout.addWidget(self.toggle_hydraulics)
        layout.addWidget(self.toggle_telemetry)
        return box

    def _clamps_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Clamps & Valves")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)

        pressure_row = QtWidgets.QHBoxLayout()
        pressure_row.addWidget(QtWidgets.QLabel("Clamp Pressure (PSI)"))
        self.clamp_pressure_input = QtWidgets.QLineEdit()
        self.clamp_pressure_input.setPlaceholderText("Enter PSI")
        self.clamp_pressure_set = QtWidgets.QLabel("--")
        self.clamp_pressure_set.setObjectName("valueLabel")
        pressure_set = QtWidgets.QPushButton("Set")
        pressure_row.addWidget(self.clamp_pressure_input)
        pressure_row.addWidget(pressure_set)
        pressure_row.addWidget(QtWidgets.QLabel("Set:"))
        pressure_row.addWidget(self.clamp_pressure_set)
        layout.addLayout(pressure_row)

        pump_row = QtWidgets.QHBoxLayout()
        pump_row.addWidget(QtWidgets.QLabel("Hydraulic Pump"))
        pump_row.addStretch(1)
        pump_row.addWidget(QtWidgets.QPushButton("On"))
        pump_row.addWidget(QtWidgets.QPushButton("Off"))
        layout.addLayout(pump_row)

        layout.addWidget(self._valve_controls("Valve 1: Propulsion Cylinders"))
        layout.addWidget(self._valve_controls("Valve 2: Clamp Cylinder"))
        layout.addWidget(self._valve_controls("Valve 3: Bidirectional Motor"))
        return box

    def _valve_controls(self, title: str) -> QtWidgets.QWidget:
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(title))
        row.addStretch(1)
        forward = QtWidgets.QRadioButton("Forward")
        neutral = QtWidgets.QRadioButton("Neutral")
        reverse = QtWidgets.QRadioButton("Reverse")
        neutral.setChecked(True)
        row.addWidget(forward)
        row.addWidget(neutral)
        row.addWidget(reverse)
        wrapper = QtWidgets.QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _connection_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Connection Status")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        self.connection_label = QtWidgets.QLabel("Disconnected")
        self.connection_label.setObjectName("statusIndicator")
        layout.addWidget(self.connection_label)
        return box

    def _stop_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Stop Buttons")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        self.estop_button = QtWidgets.QPushButton("Emergency Stop")
        self.reset_button = QtWidgets.QPushButton("Reset Systems")
        self.shutdown_time_label = QtWidgets.QLabel("Shutdown Time: 00:00")
        self.shutdown_count_label = QtWidgets.QLabel("Shutdown Count: 0")
        layout.addWidget(self.estop_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.shutdown_time_label)
        layout.addWidget(self.shutdown_count_label)
        return box

    def _launch_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Launch Buttons")
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        self.open_data_button = QtWidgets.QPushButton("Open Data Window")
        self.clear_output_button = QtWidgets.QPushButton("Clear Output Log")
        self.clear_warning_button = QtWidgets.QPushButton("Clear Warning Log")
        self.unassigned_button = QtWidgets.QPushButton("Unassigned")
        self.unassigned_button_two = QtWidgets.QPushButton("Unassigned")
        layout.addWidget(self.open_data_button)
        layout.addWidget(self.clear_output_button)
        layout.addWidget(self.clear_warning_button)
        layout.addWidget(self.unassigned_button)
        layout.addWidget(self.unassigned_button_two)
        self.open_data_button.clicked.connect(self._show_data_window)
        self.clear_output_button.clicked.connect(self.output_log.clear)
        self.clear_warning_button.clicked.connect(self.warning_log.clear)
        return box

    def _show_data_window(self) -> None:
        if self._data_window is None:
            return
        self._data_window.show()
        self._data_window.raise_()
        self._data_window.activateWindow()

    def setTelemetry(self, payload: dict) -> None:
        timestamp = payload.get("timestamp", "--")
        self.timestamp_label.setText(timestamp)
        self.status_label.setText("Telemetry online")
        self.connection_label.setText("Connected")
        self.connection_label.setProperty("status", "online")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

        system = payload.get("system", {})
        is_safe = system.get("safe", True)
        violation = system.get("violation", "")
        if is_safe:
            self.warning_log.append("System safe.")
        else:
            self.warning_log.append(f"Safety violation: {violation}")

    def setTelemetryMissing(self) -> None:
        self.status_label.setText("Waiting for telemetry")
        self.timestamp_label.setText("--")
        self.connection_label.setText("Disconnected")
        self.connection_label.setProperty("status", "offline")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)


class DataWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NABC ROV Data")
        self.resize(1400, 860)

        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        root_layout = QtWidgets.QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(16)

        header_layout = QtWidgets.QHBoxLayout()
        self.data_status_label = QtWidgets.QLabel("Waiting for telemetry")
        self.data_status_label.setObjectName("headerStatus")
        self.data_timestamp_label = QtWidgets.QLabel("--")
        self.data_timestamp_label.setObjectName("headerTimestamp")
        header_layout.addWidget(self.data_status_label)
        header_layout.addStretch(1)
        header_layout.addWidget(QtWidgets.QLabel("Last update:"))
        header_layout.addWidget(self.data_timestamp_label)
        root_layout.addLayout(header_layout)

        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setSpacing(16)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setSpacing(12)
        self.temperature_table = _build_table(["Sensor", "Temp (°C)"])
        self.rpm_label = QtWidgets.QLabel("Cutterhead RPM: --")
        self.hydraulic_pressure_label = QtWidgets.QLabel("Hydraulic Pressure: -- PSI")
        left_layout.addWidget(self._wrap_section("Temperature Sensors", self.temperature_table))
        left_layout.addWidget(self._wrap_section("Rotation", self.rpm_label))
        left_layout.addWidget(self._wrap_section("Hydraulic Motor", self.hydraulic_pressure_label))
        self.safety_indicator = QtWidgets.QLabel("Safety Relay: UNKNOWN")
        self.safety_indicator.setObjectName("safetyIndicator")
        left_layout.addWidget(self._wrap_section("Safety Relay", self.safety_indicator))
        left_layout.addStretch(1)

        middle_layout = QtWidgets.QVBoxLayout()
        middle_layout.setSpacing(12)
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setObjectName("cameraFeed")
        self.camera_label.setPixmap(_placeholder_pixmap("Camera Feed", 520, 300))
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.depth_label = QtWidgets.QLabel("Depth: --")
        self.depth_label.setObjectName("depthLabel")
        self.electrical_table = _build_table(["Channel", "Voltage", "Current"])
        middle_layout.addWidget(self._wrap_section("Live Camera", self.camera_label))
        middle_layout.addWidget(self._wrap_section("Depth", self.depth_label))
        middle_layout.addWidget(self._wrap_section("Electrical", self.electrical_table))

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setSpacing(12)
        self.pose_label = QtWidgets.QLabel("Pitch: --°  Roll: --°  Yaw: --°")
        self.pose_label.setObjectName("imuLabel")
        self.pose_image = QtWidgets.QLabel()
        self.pose_image.setPixmap(_placeholder_pixmap("Pose Visualization", 320, 200))
        self.pose_image.setAlignment(QtCore.Qt.AlignCenter)
        self.battery_label = QtWidgets.QLabel("Battery: --% | -- W | Idle")
        self.telemetry_rate_label = QtWidgets.QLabel("Telemetry Rate: -- Hz")
        self.qr_label = QtWidgets.QLabel()
        self.qr_label.setObjectName("qrCode")
        self.qr_label.setPixmap(_placeholder_pixmap("QR Code", 180, 180))
        self.qr_label.setAlignment(QtCore.Qt.AlignCenter)
        right_layout.addWidget(self._wrap_section("Orientation", self.pose_label))
        right_layout.addWidget(self._wrap_section("Trajectory", self.pose_image))
        right_layout.addWidget(self._wrap_section("Battery", self.battery_label))
        right_layout.addWidget(self._wrap_section("Telemetry Rate", self.telemetry_rate_label))
        right_layout.addWidget(self._wrap_section("Remote Access", self.qr_label))
        right_layout.addStretch(1)

        body_layout.addLayout(left_layout, 3)
        body_layout.addLayout(middle_layout, 4)
        body_layout.addLayout(right_layout, 3)

        root_layout.addLayout(body_layout, 1)

    def _wrap_section(self, title: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox()
        box.setObjectName("panelBox")
        layout = QtWidgets.QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(_section_title(title))
        layout.addWidget(widget)
        return box

    def setTelemetry(self, payload: dict) -> None:
        timestamp = payload.get("timestamp", "--")
        self.data_timestamp_label.setText(timestamp)
        self.data_status_label.setText("Telemetry online")

        sensors = payload.get("sensors", [])
        temp_rows = []
        depth_value = None
        imu_payload = None
        for sensor in sensors:
            name = sensor.get("name", "--")
            value = sensor.get("value", "--")
            units = sensor.get("units", "")
            if "temp" in str(name).lower():
                temp_rows.append([
                    str(name),
                    f"{value:.2f}" if isinstance(value, (int, float)) else str(value),
                ])
            if "depth" in str(name).lower():
                depth_value = value
            if "imu" in str(name).lower():
                imu_payload = sensor.get("imu")

        if temp_rows:
            _update_table(self.temperature_table, temp_rows)

        if depth_value is not None:
            self.depth_label.setText(f"Depth: {depth_value:.2f}")

        if imu_payload:
            roll = imu_payload.get("roll", 0.0)
            pitch = imu_payload.get("pitch", 0.0)
            yaw = imu_payload.get("yaw", 0.0)
            self.pose_label.setText(
                f"Pitch: {pitch:.1f}°  Roll: {roll:.1f}°  Yaw: {yaw:.1f}°"
            )

        system = payload.get("system", {})
        is_safe = system.get("safe", True)
        if is_safe:
            self.safety_indicator.setText("Safety Relay: GREEN")
            self.safety_indicator.setProperty("status", "safe")
        else:
            self.safety_indicator.setText("Safety Relay: RED")
            self.safety_indicator.setProperty("status", "fault")
        self.safety_indicator.style().unpolish(self.safety_indicator)
        self.safety_indicator.style().polish(self.safety_indicator)

    def setTelemetryMissing(self) -> None:
        self.data_status_label.setText("Waiting for telemetry")
        self.data_timestamp_label.setText("--")


def apply_theme(app: QtWidgets.QApplication) -> None:
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#101827"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#E2E8F0"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#0F172A"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#111B2E"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#E2E8F0"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#111827"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#E2E8F0"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#1F2937"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#E2E8F0"))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#38BDF8"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#0F172A"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QLabel#headerStatus { font-size: 20px; font-weight: 600; }
        QLabel#headerTimestamp { font-size: 13px; color: #94A3B8; }
        QLabel#sectionTitle { font-size: 16px; font-weight: 600; }
        QLabel#imuLabel { font-size: 14px; color: #E2E8F0; }
        QLabel#runtimeLabel { font-size: 24px; font-weight: 700; }
        QLabel#valueLabel { font-size: 14px; color: #E2E8F0; }
        QFrame#statusCard {
            background: #111827;
            border: 1px solid #1E293B;
            border-radius: 12px;
        }
        QGroupBox#panelBox {
            border: 1px solid #1E293B;
            border-radius: 12px;
            margin-top: 8px;
        }
        QGroupBox#panelBox::title { color: #94A3B8; }
        QLabel#statusIndicator {
            font-size: 14px;
            font-weight: 600;
            padding: 6px;
            border-radius: 8px;
            background: #1F2937;
        }
        QLabel#statusIndicator[status="online"] { background: #0F766E; }
        QLabel#statusIndicator[status="offline"] { background: #7F1D1D; }
        QLabel#safetyIndicator {
            font-size: 14px;
            font-weight: 600;
            padding: 6px;
            border-radius: 8px;
            background: #1F2937;
        }
        QLabel#safetyIndicator[status="safe"] { background: #15803D; }
        QLabel#safetyIndicator[status="fault"] { background: #B91C1C; }
        QTextEdit#outputLog { color: #22C55E; }
        QTextEdit#warningLog { color: #EF4444; }
        QLabel#cardTitle { font-size: 12px; color: #94A3B8; }
        QLabel#cardValue { font-size: 18px; font-weight: 600; }
        QTableWidget#dataTable {
            border: 1px solid #1E293B;
            background: #0F172A;
        }
        QHeaderView::section {
            background: #1E293B;
            color: #E2E8F0;
            padding: 6px;
            border: none;
        }
        """
    )


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    apply_theme(app)

    control_window = ControlWindow()
    data_window = DataWindow()
    control_window.set_data_window(data_window)
    control_window.show()

    reader = TelemetryReader(TELEMETRY_PATH)
    reader.telemetryUpdated.connect(control_window.setTelemetry)
    reader.telemetryUpdated.connect(data_window.setTelemetry)
    reader.telemetryMissing.connect(control_window.setTelemetryMissing)
    reader.telemetryMissing.connect(data_window.setTelemetryMissing)
    reader.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
