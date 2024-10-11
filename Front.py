import datetime
import json
import os.path
import sys
import threading
import time

import schedule
from PyQt6.QtGui import QIcon, QAction
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QPushButton,
    QLabel,
    QCheckBox,
    QVBoxLayout,
    QLineEdit,
    QGridLayout,
    QFileDialog,
    QDialog,
    QSystemTrayIcon,
    QMenu,


)
from requests import HTTPError

import Authentication
import ReportCreator
import Requests

global mainWindow
global loginStatus


class LoginWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        layout = QVBoxLayout()

        self.loginLineEdit = QLineEdit("Login")
        self.passwordLineEdit = QLineEdit("Password")
        self.rememberCheckbox = QCheckBox("Remember me?")
        self.rememberCheckbox.setCheckState(Qt.CheckState.Unchecked)
        data = self.fillData()
        self.loginLineEdit.setText(data[0])
        self.passwordLineEdit.setText(data[1])

        self.passwordLineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        button = QPushButton("Login")
        button.clicked.connect(self.login)

        registerButton = QPushButton('Register')
        registerButton.clicked.connect(self.createRegisterWindow)


        layout.addWidget(self.loginLineEdit)
        layout.addWidget(self.passwordLineEdit)
        layout.addWidget(self.rememberCheckbox)
        layout.addWidget(button)
        layout.addWidget(registerButton)

        self.setLayout(layout)
        self.setMinimumSize(300, 150)

    def createRegisterWindow(self):
        registerWindow = RegisterWindow()
        registerWindow.show()


    def fillData(self):
        file = open("data/auth-params.json")
        auth_params = json.load(file)
        login = auth_params.get('login')
        password = auth_params.get('password')
        return [login, password]

    # def closeEvent(self, event):
    #     print('close2')
    #     for window in QApplication.topLevelWidgets():
    #         window.close()

    def login(self):

        if (Authentication.LoginUser(self.loginLineEdit.text(), self.passwordLineEdit.text())) is not None:
            loginStatus = True
        # if error code is not valid then dont write
        if (self.rememberCheckbox.checkState() == Qt.CheckState.Checked):
            print('asaasaa')
            file = open("data/auth-params.json", "w")
            data = {'login': self.loginLineEdit.text(), 'password': self.passwordLineEdit.text()}
            obj = json.dumps(data, indent=2)
            file.write(obj)
            file.close()
        self.setEnabled(False)
        self.close()
        print('main')
        mainWindow.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.time = "00:00"
        self.ui = uic.loadUi('data/mainwindow.ui', self)
        self.ui.selectFileButton.clicked.connect(self.buttonClick)
        self.ui.createReportButton.clicked.connect(lambda: ReportCreator.createDailyReport(self.file, float(self.ui.plainTextEdit.toPlainText())))
        self.ui.startThreadButton.clicked.connect(self.threadingStart)
        self.ui.stopThreadButton.clicked.connect(self.stopEvent)

        self.trayIcon = QSystemTrayIcon(QIcon('data\icon.png'), self)
        self.trayIcon.show()
        self.trayIcon.activated.connect(self.trayActivated)
        menu = QMenu()
        exit = menu.addAction('EXIT')
        exit.triggered.connect(self.exitEvent)
        self.trayIcon.setContextMenu(menu)
        self.ui.reportDoneLine.setVisible(False)

    def stopEvent(self):
        self.stop_event.set()

    def exitEvent(self):
        self.stop_event.set()
        self.close()
        self.trayIcon.setVisible(False)
        app.quit()

    def trayActivated(self, reason):
        if reason == self.trayIcon.ActivationReason.Trigger:
            if loginWindow.isEnabled():
                loginWindow.show()
            else:
                mainWindow.show()

    def createDalyReportSchedule(self, stop_event):
        state = True
        while state and not stop_event.is_set():
            reportTime = self.ui.timeEdit.time().toString()[0:5]
            print(self.file, datetime.datetime.now(), reportTime)
            if len(schedule.get_jobs()) != 1:
                schedule.clear()
                schedule.every().day.at(reportTime).do(ReportCreator.createDailyReport, (self.file, float(self.ui.plainTextEdit.toPlainText())))
            elif schedule.get_jobs()[0].next_run.time().strftime('%H:%M') != reportTime:
                schedule.clear()
                schedule.every().day.at(reportTime).do(ReportCreator.createDailyReport, self.file)
            print(schedule.get_jobs())
            schedule.run_pending()
            print(ReportCreator.reportDone)
            if ReportCreator.reportDone:
                self.ui.reportDoneLine.setText("Report created " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                self.ui.reportDoneLine.setVisible(True)
                ReportCreator.reportDone = False
            time.sleep(60)

    def threadingStart(self):
        self.stop_event = threading.Event()
        self.c_thread = threading.Thread(target=self.createDalyReportSchedule, args=(self.stop_event, ))
        self.c_thread.start()


    def buttonClick(self):
        filter = "xls(*.xls *.xlsx)"
        self.file = QFileDialog.getOpenFileName(self, 'Select file', filter=filter)[0]
        self.ui.filenameTextLine.setText(os.path.basename(self.file))
        print(self.file)

class RegisterWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Register user')
        layout = QVBoxLayout()
        self.loginLineEdit = QLineEdit()
        self.passwordLineEdit = QLineEdit()

        button = QPushButton("Register")
        button.clicked.connect(lambda: self.register(self.loginLineEdit.text(), self.passwordLineEdit.text()))

        layout.addWidget(self.loginLineEdit)
        layout.addWidget(self.passwordLineEdit)
        layout.addWidget(button)

        self.setLayout(layout)
        self.setMinimumSize(300, 150)

    def register(self, login, password):
        try:
            Authentication.RegisterNewUser(login, password)
            self.close()
        except HTTPError as e:
            errorBox = QtWidgets.QMessageBox()
            errorBox.setText("WRONG LOGIN OR PASSWORD")
            errorBox.exec()

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
mainWindow = MainWindow()
loginWindow = LoginWindow()
loginWindow.show()
sys.exit(app.exec())

