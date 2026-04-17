# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
import os
os.system("pyside6-uic mainwindow.ui -o ui_mainwindow.py")  # regenerate
os.system("pyside6-uic datawindow.ui -o ui_datawindow.py")
os.system("python main2.py")  # run script
