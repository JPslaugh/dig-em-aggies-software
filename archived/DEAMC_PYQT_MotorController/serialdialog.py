from ui_serialdialog import Ui_Dialog
from PySide6.QtWidgets import QDialog

class SerialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def get_port(self):
        return self.ui.port.text()

    def get_baudrate(self):
        return self.ui.baudrate.text()

    def get_timeout(self):
        return self.ui.timeout.text()
