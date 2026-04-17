# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'datawindow.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QMenuBar,
    QSizePolicy, QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(720, 520)
        MainWindow.setMinimumSize(QSize(720, 520))
        MainWindow.setStyleSheet(u"background-color: rgb(85, 0, 0);")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.frame.setLineWidth(0)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_2.setLineWidth(0)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_4 = QFrame(self.frame_2)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_4.setLineWidth(0)
        self.gridLayout_2 = QGridLayout(self.frame_4)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 2, 0)
        self.groupBox = QGroupBox(self.frame_4)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.gridLayout_4 = QGridLayout(self.groupBox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        font = QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)

        self.gridLayout_4.addWidget(self.label_5, 3, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.gridLayout_4.addWidget(self.label_3, 1, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout_4.addWidget(self.label_4, 2, 0, 1, 1)

        self.temp1 = QLabel(self.groupBox)
        self.temp1.setObjectName(u"temp1")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.temp1.setFont(font1)
        self.temp1.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.temp1, 0, 1, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font)

        self.gridLayout_4.addWidget(self.label_6, 4, 0, 1, 1)

        self.temp2 = QLabel(self.groupBox)
        self.temp2.setObjectName(u"temp2")
        self.temp2.setFont(font1)
        self.temp2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.temp2, 1, 1, 1, 1)

        self.temp3 = QLabel(self.groupBox)
        self.temp3.setObjectName(u"temp3")
        self.temp3.setFont(font1)
        self.temp3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.temp3, 2, 1, 1, 1)

        self.temp4 = QLabel(self.groupBox)
        self.temp4.setObjectName(u"temp4")
        self.temp4.setFont(font1)
        self.temp4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.temp4, 3, 1, 1, 1)

        self.temp5 = QLabel(self.groupBox)
        self.temp5.setObjectName(u"temp5")
        self.temp5.setFont(font1)
        self.temp5.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.temp5, 4, 1, 1, 1)


        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.frame_4)

        self.frame_5 = QFrame(self.frame_2)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_5.setLineWidth(0)
        self.gridLayout_3 = QGridLayout(self.frame_5)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 2, 0)
        self.groupBox_2 = QGroupBox(self.frame_5)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.gridLayout_5 = QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setFont(font)

        self.gridLayout_5.addWidget(self.label_14, 2, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font)

        self.gridLayout_5.addWidget(self.label_12, 1, 0, 1, 1)

        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setFont(font)

        self.gridLayout_5.addWidget(self.label_15, 3, 0, 1, 1)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font)

        self.gridLayout_5.addWidget(self.label_11, 0, 0, 1, 1)

        self.pres2 = QLabel(self.groupBox_2)
        self.pres2.setObjectName(u"pres2")
        self.pres2.setFont(font1)
        self.pres2.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.pres2, 1, 1, 1, 1)

        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setFont(font)

        self.gridLayout_5.addWidget(self.label_16, 4, 0, 1, 1)

        self.pres1 = QLabel(self.groupBox_2)
        self.pres1.setObjectName(u"pres1")
        self.pres1.setFont(font1)
        self.pres1.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.pres1, 0, 1, 1, 1)

        self.pres3 = QLabel(self.groupBox_2)
        self.pres3.setObjectName(u"pres3")
        self.pres3.setFont(font1)
        self.pres3.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.pres3, 2, 1, 1, 1)

        self.pres4 = QLabel(self.groupBox_2)
        self.pres4.setObjectName(u"pres4")
        self.pres4.setFont(font1)
        self.pres4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.pres4, 3, 1, 1, 1)

        self.pres5 = QLabel(self.groupBox_2)
        self.pres5.setObjectName(u"pres5")
        self.pres5.setFont(font1)
        self.pres5.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_5.addWidget(self.pres5, 4, 1, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.frame_5)

        self.frame_6 = QFrame(self.frame_2)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_6.setLineWidth(0)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 2, 0)
        self.groupBox_3 = QGroupBox(self.frame_6)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.gridLayout_10 = QGridLayout(self.groupBox_3)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.wattage = QLabel(self.groupBox_3)
        self.wattage.setObjectName(u"wattage")
        self.wattage.setFont(font1)
        self.wattage.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_10.addWidget(self.wattage, 0, 1, 1, 1)

        self.label_21 = QLabel(self.groupBox_3)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setFont(font)

        self.gridLayout_10.addWidget(self.label_21, 0, 0, 1, 1)

        self.label_23 = QLabel(self.groupBox_3)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setFont(font)

        self.gridLayout_10.addWidget(self.label_23, 1, 0, 1, 1)

        self.charge = QLabel(self.groupBox_3)
        self.charge.setObjectName(u"charge")
        self.charge.setFont(font1)
        self.charge.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_10.addWidget(self.charge, 1, 1, 1, 1)


        self.horizontalLayout_2.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(self.frame_6)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.gridLayout_11 = QGridLayout(self.groupBox_4)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.label_31 = QLabel(self.groupBox_4)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setFont(font)

        self.gridLayout_11.addWidget(self.label_31, 0, 0, 1, 1)

        self.acv = QLabel(self.groupBox_4)
        self.acv.setObjectName(u"acv")
        self.acv.setFont(font1)
        self.acv.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_11.addWidget(self.acv, 0, 1, 1, 1)

        self.label_33 = QLabel(self.groupBox_4)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setFont(font)

        self.gridLayout_11.addWidget(self.label_33, 1, 0, 1, 1)

        self.dcv = QLabel(self.groupBox_4)
        self.dcv.setObjectName(u"dcv")
        self.dcv.setFont(font1)
        self.dcv.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_11.addWidget(self.dcv, 1, 1, 1, 1)


        self.horizontalLayout_2.addWidget(self.groupBox_4)


        self.verticalLayout.addWidget(self.frame_6)

        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 2)
        self.verticalLayout.setStretch(2, 1)

        self.horizontalLayout.addWidget(self.frame_2)

        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_3.setLineWidth(0)
        self.verticalLayout_2 = QVBoxLayout(self.frame_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame_9 = QFrame(self.frame_3)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_9.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_9.setLineWidth(0)
        self.gridLayout_6 = QGridLayout(self.frame_9)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(2, 0, 0, 0)
        self.groupBox_5 = QGroupBox(self.frame_9)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setStyleSheet(u"background-color: rgb(48, 0, 0);")

        self.gridLayout_6.addWidget(self.groupBox_5, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_9)

        self.frame_7 = QFrame(self.frame_3)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_13 = QGridLayout(self.frame_7)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.gridLayout_13.setContentsMargins(2, 0, 0, 0)
        self.groupBox_9 = QGroupBox(self.frame_7)
        self.groupBox_9.setObjectName(u"groupBox_9")
        self.groupBox_9.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.horizontalLayout_5 = QHBoxLayout(self.groupBox_9)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_35 = QLabel(self.groupBox_9)
        self.label_35.setObjectName(u"label_35")
        self.label_35.setFont(font)

        self.horizontalLayout_5.addWidget(self.label_35)

        self.rpm = QLabel(self.groupBox_9)
        self.rpm.setObjectName(u"rpm")
        self.rpm.setFont(font1)
        self.rpm.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.rpm)


        self.gridLayout_13.addWidget(self.groupBox_9, 0, 0, 1, 1)

        self.groupBox_10 = QGroupBox(self.frame_7)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.groupBox_10.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.horizontalLayout_6 = QHBoxLayout(self.groupBox_10)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_37 = QLabel(self.groupBox_10)
        self.label_37.setObjectName(u"label_37")
        self.label_37.setFont(font)

        self.horizontalLayout_6.addWidget(self.label_37)

        self.deg = QLabel(self.groupBox_10)
        self.deg.setObjectName(u"deg")
        self.deg.setFont(font1)
        self.deg.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.deg)


        self.gridLayout_13.addWidget(self.groupBox_10, 0, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_7)

        self.frame_10 = QFrame(self.frame_3)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_10.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_10.setLineWidth(0)
        self.gridLayout_7 = QGridLayout(self.frame_10)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(2, 0, 0, 0)
        self.groupBox_6 = QGroupBox(self.frame_10)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_25 = QLabel(self.groupBox_6)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setFont(font)

        self.horizontalLayout_4.addWidget(self.label_25)

        self.relay = QLabel(self.groupBox_6)
        self.relay.setObjectName(u"relay")
        self.relay.setFont(font)
        self.relay.setStyleSheet(u"background-color: rgb(0, 255, 0);")
        self.relay.setAlignment(Qt.AlignmentFlag.AlignJustify|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.relay)

        self.horizontalLayout_4.setStretch(0, 9)
        self.horizontalLayout_4.setStretch(1, 1)

        self.gridLayout_7.addWidget(self.groupBox_6, 0, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_10)

        self.frame_11 = QFrame(self.frame_3)
        self.frame_11.setObjectName(u"frame_11")
        self.frame_11.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_11.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_11.setLineWidth(0)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_11)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(2, 0, 0, 0)
        self.frame_12 = QFrame(self.frame_11)
        self.frame_12.setObjectName(u"frame_12")
        self.frame_12.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_12.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_12.setLineWidth(0)
        self.gridLayout_8 = QGridLayout(self.frame_12)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.groupBox_7 = QGroupBox(self.frame_12)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setStyleSheet(u"background-color: rgb(48, 0, 0);")
        self.gridLayout_12 = QGridLayout(self.groupBox_7)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.label_27 = QLabel(self.groupBox_7)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setFont(font)

        self.gridLayout_12.addWidget(self.label_27, 0, 0, 1, 1)

        self.upload = QLabel(self.groupBox_7)
        self.upload.setObjectName(u"upload")
        self.upload.setFont(font1)
        self.upload.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_12.addWidget(self.upload, 0, 1, 1, 1)

        self.label_29 = QLabel(self.groupBox_7)
        self.label_29.setObjectName(u"label_29")
        self.label_29.setFont(font)

        self.gridLayout_12.addWidget(self.label_29, 1, 0, 1, 1)

        self.download = QLabel(self.groupBox_7)
        self.download.setObjectName(u"download")
        self.download.setFont(font1)
        self.download.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_12.addWidget(self.download, 1, 1, 1, 1)


        self.gridLayout_8.addWidget(self.groupBox_7, 0, 0, 1, 1)


        self.horizontalLayout_3.addWidget(self.frame_12)

        self.frame_13 = QFrame(self.frame_11)
        self.frame_13.setObjectName(u"frame_13")
        self.frame_13.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_13.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_13.setLineWidth(0)
        self.gridLayout_9 = QGridLayout(self.frame_13)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setHorizontalSpacing(0)
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.groupBox_8 = QGroupBox(self.frame_13)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.groupBox_8.setStyleSheet(u"background-color: rgb(48, 0, 0);")

        self.gridLayout_9.addWidget(self.groupBox_8, 0, 0, 1, 1)


        self.horizontalLayout_3.addWidget(self.frame_13)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.frame_11)

        self.verticalLayout_2.setStretch(0, 3)
        self.verticalLayout_2.setStretch(1, 1)
        self.verticalLayout_2.setStretch(2, 1)
        self.verticalLayout_2.setStretch(3, 2)

        self.horizontalLayout.addWidget(self.frame_3)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 3)

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 720, 17))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Temperature", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Temperature 4", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Temperature 2", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Temperature 3", None))
        self.temp1.setText(QCoreApplication.translate("MainWindow", u"0.0 deg F", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Temperature 1", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Temperature 5", None))
        self.temp2.setText(QCoreApplication.translate("MainWindow", u"0.0 deg F", None))
        self.temp3.setText(QCoreApplication.translate("MainWindow", u"0.0 deg F", None))
        self.temp4.setText(QCoreApplication.translate("MainWindow", u"0.0 deg F", None))
        self.temp5.setText(QCoreApplication.translate("MainWindow", u"0.0 deg F", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Pressure", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Pressure 3", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Pressure 2", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Pressure 4", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Pressure 1", None))
        self.pres2.setText(QCoreApplication.translate("MainWindow", u"0.0 psi", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Pressure 5", None))
        self.pres1.setText(QCoreApplication.translate("MainWindow", u"0.0 psi", None))
        self.pres3.setText(QCoreApplication.translate("MainWindow", u"0.0 psi", None))
        self.pres4.setText(QCoreApplication.translate("MainWindow", u"0.0 psi", None))
        self.pres5.setText(QCoreApplication.translate("MainWindow", u"0.0 psi", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Battery", None))
        self.wattage.setText(QCoreApplication.translate("MainWindow", u"0 W", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Power", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Charge", None))
        self.charge.setText(QCoreApplication.translate("MainWindow", u"0%", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("MainWindow", u"Voltage", None))
        self.label_31.setText(QCoreApplication.translate("MainWindow", u"AC Voltage", None))
        self.acv.setText(QCoreApplication.translate("MainWindow", u"0 V", None))
        self.label_33.setText(QCoreApplication.translate("MainWindow", u"DC Voltage", None))
        self.dcv.setText(QCoreApplication.translate("MainWindow", u"0 V", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("MainWindow", u"Camera", None))
        self.groupBox_9.setTitle(QCoreApplication.translate("MainWindow", u"Rotation", None))
        self.label_35.setText(QCoreApplication.translate("MainWindow", u"speed", None))
        self.rpm.setText(QCoreApplication.translate("MainWindow", u"0 rpm", None))
        self.groupBox_10.setTitle(QCoreApplication.translate("MainWindow", u"Twist", None))
        self.label_37.setText(QCoreApplication.translate("MainWindow", u"deviation", None))
        self.deg.setText(QCoreApplication.translate("MainWindow", u"0 deg", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("MainWindow", u"Safety Relays", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Safety Relay Status", None))
        self.relay.setText("")
        self.groupBox_7.setTitle(QCoreApplication.translate("MainWindow", u"Data Transfer", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Upload", None))
        self.upload.setText(QCoreApplication.translate("MainWindow", u"0 Mbps", None))
        self.label_29.setText(QCoreApplication.translate("MainWindow", u"Download", None))
        self.download.setText(QCoreApplication.translate("MainWindow", u"0 Mbps", None))
        self.groupBox_8.setTitle(QCoreApplication.translate("MainWindow", u"QR Code", None))
    # retranslateUi

