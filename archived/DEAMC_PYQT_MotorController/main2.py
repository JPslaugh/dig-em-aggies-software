import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
)

# Import generated UI class
from ui_mainwindow import Ui_MainWindow
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIntValidator

from datawindow import DataWindow
from serialdialog import SerialDialog
# import serial

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create UI object
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setEnabled(True)

        # Put your code here 👇
        self.setup_connections()

        self.data_window = None
        self.serial_window = None

        # Initial Conditions
        self.enable(self.ui.stopButton, 0)
        self.enable(self.ui.liq_on, 0)
        self.enable(self.ui.hyd_on, 0)
        self.enable(self.ui.ele_on, 0)
        self.enable(self.ui.smt_on, 0)
        self.enable(self.ui.forward, 0)
        self.enable(self.ui.neutral, 0)
        self.enable(self.ui.reverse, 0)
        self.enable(self.ui.reset, 0)

        # Variables
        self.isRunning = False
        self.liq = 0
        self.hyd = 0
        self.ele = 0
        self.smt = 0
        self.stopCount = 0

        # Serial
        self.port = ""
        self.baudrate = 0
        self.timeout = 0

        # Limits
        rpmLimits = QIntValidator(0, 100, self)
        psiLimits = QIntValidator(0, 10, self)
        self.ui.rpmEdit.setValidator(rpmLimits)
        self.ui.psiEdit.setValidator(psiLimits)

        # Timer Code
        self.seconds = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        # Create variable names for ui element
        self.warningLog = self.ui.warningLog
        self.outputLog = self.ui.outputLog

        # Change background color of logs
        self.warningLog.setStyleSheet("color: red; background-color: black")
        self.outputLog.setStyleSheet("color: green; background-color: black")

    def setup_connections(self):
        # Example: connect a button
        self.ui.runButton.clicked.connect(self.run)
        self.ui.stopButton.clicked.connect(self.stop_func)
        self.ui.rpmEdit.returnPressed.connect(self.updateRPM)
        self.ui.psiEdit.returnPressed.connect(self.updatePSI)
        self.ui.eStop.clicked.connect(self.eStop_func)
        self.ui.reset.clicked.connect(self.reset_func)
        self.ui.liq_on.clicked.connect(self.liq_func)
        self.ui.hyd_on.clicked.connect(self.hyd_func)
        self.ui.ele_on.clicked.connect(self.ele_func)
        self.ui.smt_on.clicked.connect(self.smt_func)
        self.ui.forward.clicked.connect(self.forward_func)
        self.ui.neutral.clicked.connect(self.neutral_func)
        self.ui.reverse.clicked.connect(self.reverse_func)
        self.ui.dataLaunch.clicked.connect(self.dataWindow)
        self.ui.clearOutput.clicked.connect(self.clearOutput)
        self.ui.clearWarning.clicked.connect(self.clearWarning)
        self.ui.serial.clicked.connect(self.serialWindow)




    # Log functions
    def printToOutput(self, text):
        self.outputLog.appendPlainText(text)

    def printToWarning(self, text):
        self.warningLog.appendPlainText(text)

    # Runtime Functions
    def run(self):
        self.printToOutput("Program started")
        self.isRunning = True
        self.startTimer()

        self.enable(self.ui.stopButton, 1)
        self.enable(self.ui.runButton, 0)
        self.setAll(1)

    def stop_func(self):
        self.printToOutput("Program halted by user")
        self.isRunning = False
        self.stopTimer()
        self.printToOutput("Total time ran: " + str(self.ui.runtimeLabel.text()))
        self.resetTimer()

        self.enable(self.ui.runButton, 1)
        self.enable(self.ui.stopButton, 0)
        self.updateRPM()
        self.updatePSI()
        self.setAll(0)

    def eStop_func(self):
        if self.isRunning == True:
            self.printToWarning("EMERGENCY STOP ACTIVATED; ENSURE ALL SYSTEMS ARE SECURE BEFORE RESETTING")
            self.stop_func()
            self.startTimer()
            self.stopCount += 1

            self.enable(self.ui.reset, 1)
            self.enable(self.ui.runButton, 0)
            self.setAll(0)
        else:
            self.printToOutput("Emergency can only be activated if Program is running")

    def reset_func(self):
        self.printToOutput("Systems have been reset")
        self.stopTimer()
        self.ui.stopCount.setText("Count: " + str(self.stopCount))
        self.resetTimer()

        self.enable(self.ui.runButton, 1)
        self.enable(self.ui.reset, 0)


    # Functions while is running
    def liq_func(self):
        if self.liq == 1:
            self.printToOutput("Liquid injectors enabled")
            self.ui.liq_on.setText("On")
            self.ui.liq_on.setStyleSheet("background-color: rgb(85,0,0); color: lime")
            self.liq = 0
        else:
            self.printToOutput("Liquid injectors disabled")
            self.ui.liq_on.setText("Off")
            self.ui.liq_on.setStyleSheet("background-color: rgb(85,0,0); color: white")
            self.liq = 1

    def hyd_func(self):
        if self.hyd == 1:
            self.printToOutput("Hydraulics enabled")
            self.ui.hyd_on.setText("On")
            self.ui.hyd_on.setStyleSheet("background-color: rgb(85,0,0); color: lime")
            self.hyd = 0
        else:
            self.printToOutput("Hydraulics disabled")
            self.ui.hyd_on.setText("Off")
            self.ui.hyd_on.setStyleSheet("background-color: rgb(85,0,0); color: white")
            self.hyd = 1

    def ele_func(self):
        if self.ele == 1:
            self.printToOutput("Electronics enabled")
            self.ui.ele_on.setText("On")
            self.ui.ele_on.setStyleSheet("background-color: rgb(85,0,0); color: lime")
            self.ele = 0
        else:
            self.printToOutput("Electronics disabled")
            self.ui.ele_on.setText("Off")
            self.ui.ele_on.setStyleSheet("background-color: rgb(85,0,0); color: white")
            self.ele = 1

    def smt_func(self):
        if self.smt == 1:
            self.printToOutput("Something enabled")
            self.ui.smt_on.setText("On")
            self.ui.smt_on.setStyleSheet("background-color: rgb(85,0,0); color: lime")
            self.smt = 0
        else:
            self.printToOutput("Something disabled")
            self.ui.smt_on.setText("Off")
            self.ui.smt_on.setStyleSheet("background-color: rgb(85,0,0); color: white")
            self.smt = 1

    def forward_func(self):
        self.printToOutput("Actuators set to forward")

    def neutral_func(self):
        self.printToOutput("Actuators set to neutral")

    def reverse_func(self):
        self.printToOutput("Actuators set to reverse")

    # Function for updating values
    def updateRPM(self):
        if self.isRunning == True:
            self.ui.rpmLabel.setText(self.ui.rpmEdit.text() + " rpm")
            self.printToOutput("motor set to " + self.ui.rpmEdit.text() + " rpm")
            self.ui.rpmEdit.clear()
        else:
            self.printToOutput("Program is not running")
            self.ui.rpmLabel.setText("0 rpm")

    def updatePSI(self):
        if self.isRunning == True:
            self.ui.psiLabel.setText(self.ui.psiEdit.text() + " psi")
            self.printToOutput("guage set to " + self.ui.psiEdit.text() + " psi")
            self.ui.psiEdit.clear()
        else:
            self.printToOutput("Program is not running")
            self.ui.psiLabel.setText("0 psi")

        # Launch button functions
    def dataWindow(self):
        if self.data_window == None:
            self.data_window = DataWindow()
        self.data_window.show()
        self.data_window.raise_()
        self.data_window.activateWindow()

    def serialWindow(self):
        dialog = SerialDialog(self)
        result = dialog.exec()

        if result == SerialDialog.Accepted:
            self.port = dialog.get_port()
            self.printToOutput(str(self.port) + " set as Serial port")
            self.baudrate = dialog.get_baudrate()
            self.printToOutput(str(self.baudrate) + " set as Baudrate")
            self.timeout = dialog.get_timeout()
            self.printToOutput(str(self.timeout) + " set as timeout")

        # ser = serial.Serial(
        #     port=self.port,
        #     baudrate=self.baudrate,
        #     timeout=self.timeout
        # )

        # ser.write(b"HELLO\n")

    def clearOutput(self):
        self.ui.outputLog.clear()

    def clearWarning(self):
        self.ui.warningLog.clear()

        # Extra functions for handling
    def enable(self, button, set):
        if set == 0:
            button.setEnabled(False)
            button.setStyleSheet("background-color: dark-gray; color:gray")
        else:
            button.setEnabled(True)
            button.setStyleSheet("background-color: rgb(85,0,0); color:white")

    def setAll(self, set):
        if set == 0:
            self.liq = 0
            self.hyd = 0
            self.ele = 0
            self.smt = 0
            self.neutral_func()
            self.liq_func()
            self.hyd_func()
            self.ele_func()
            self.smt_func()
            self.enable(self.ui.liq_on, 0)
            self.enable(self.ui.hyd_on, 0)
            self.enable(self.ui.ele_on, 0)
            self.enable(self.ui.smt_on, 0)
            self.enable(self.ui.forward, 0)
            self.enable(self.ui.neutral, 0)
            self.enable(self.ui.reverse, 0)

        elif set == 1:
            self.liq = 1
            self.hyd = 1
            self.ele = 1
            self.smt = 1
            self.enable(self.ui.liq_on, 1)
            self.enable(self.ui.hyd_on, 1)
            self.enable(self.ui.ele_on, 1)
            self.enable(self.ui.smt_on, 1)
            self.enable(self.ui.forward, 1)
            self.enable(self.ui.neutral, 1)
            self.enable(self.ui.reverse, 1)

    def update_time(self):
        self.seconds += 1
        hours = self.seconds // 3600
        minutes = (self.seconds % 3600) // 60
        secs = self.seconds % 60

        self.timerStr = f"{hours:02}:{minutes:02}:{secs:02}"

        if self.isRunning == True:
            self.ui.runtimeLabel.setText(self.timerStr)
        else:
            self.ui.stoptimeLabel.setText("Time: " + self.timerStr)

    def startTimer(self):
        self.timer.start(1000)  # 1000 ms = 1 second

    def stopTimer(self):
        self.timer.stop()

    def resetTimer(self):
        self.timer.stop()
        self.seconds = 0
        if self.isRunning == True:
            self.ui.estopLabel.setText("00:00:00")
        else:
            self.ui.runtimeLabel.setText("00:00:00")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
