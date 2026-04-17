from ui_datawindow import Ui_MainWindow
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QTimer

class DataWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.seconds = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)

        self.timer.start(1000)

        # Variables
        self.variables = [
            ("temp1", 0.0, " F"),
            ("temp2", 1.0, " F"),
            ("temp3", 0.0, " F"),
            ("temp4", 0.0, " F"),
            ("temp5", 0.0, " F"),
            ("pres1", 0.0, " deg F"),
            ("pres2", 3.0, " deg F"),
            ("pres3", 0.0, " deg F"),
            ("pres4", 0.0, " deg F"),
            ("pres5", 0.0, " deg F"),
            ("wattage", 0.0, " W"),
            ("charge", 0, "%"),
            ("acv", 0.0, " V"),
            ("dcv", 0.0, " V"),
            ("rpm", 0.0, " rpm"),
            ("deg", 0.0, " deg"),
            ("upload", 0.0, "Mbps"),
            ("download", 0.0, "Mbps"),
        ]

        self.labels = []

        for name, value, suffix in self.variables:
            label = getattr(self.ui, name, None)
            if label:
                self.labels.append([label, value, suffix])

    def update(self): # called every second

        # Update a value example
        self.labels[0][1] += 1
        self.labels[15][1] += 2

        for label, value, suffix in self.labels:
            label.setText(f"{value}{suffix}")
