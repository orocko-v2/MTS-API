import configparser
import datetime
import os.path
import sys
import threading
import time

import schedule
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QFileDialog,
    QDialog,
    QSystemTrayIcon,
    QMenu,
    QTextEdit
)

from requests import HTTPError

import Authentication
import ReportCreator
import config_path_file
from Exceptions import WrongPasswordException, WrongLoginException, DatabaseConnectionException

global mainWindow
global loginStatus


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему")
        layout = QVBoxLayout()

        self.loginLineEdit = QLineEdit()
        self.passwordLineEdit = QLineEdit()
        self.passwordLineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        button = QPushButton("Войти в аккаунт")
        button.clicked.connect(self.loginUser)

        settingsButton = QPushButton('Настройки')
        settingsButton.clicked.connect(self.openSettings)

        registerButton = QPushButton('Зарегистрировать')
        registerButton.clicked.connect(self.createRegisterWindow)

        layout.addWidget(self.loginLineEdit)
        layout.addWidget(self.passwordLineEdit)
        layout.addWidget(button)
        layout.addWidget(registerButton)
        layout.addWidget(settingsButton)

        self.setLayout(layout)
        self.setMinimumSize(300, 150)

    def openSettings(self):
        settingsWindow = SettingsWindow(self)
        settingsWindow.show()

    def createRegisterWindow(self):
        registerWindow = RegisterWindow()
        registerWindow.show()

    def login(self):
        if (Authentication.LoginUser(self.loginLineEdit.text(), self.passwordLineEdit.text())) is not None:
            self.setEnabled(False)
            self.close()
            mainWindow.show()
        else:
            raise WrongPasswordException()

    def loginUser(self):
        try:
            self.login()
        except WrongPasswordException as ePass:
            errorBox = QtWidgets.QMessageBox()
            errorBox.setText("Неправильный пароль")
            errorBox.exec()
        except WrongLoginException as eLogin:
            errorBox = QtWidgets.QMessageBox()
            errorBox.setText("Неверный логин")
            errorBox.exec()
        except DatabaseConnectionException as eConn:
            errorBox = QtWidgets.QMessageBox()
            errorBox.setText("Нет доступа к базе данных")
            errorBox.exec()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.time = "00:00"
        self.ui = uic.loadUi('data/mainwindow.ui', self)
        self.ui.selectFileButton.clicked.connect(self.buttonClick)
        self.ui.createReportButton.clicked.connect(
            lambda: ReportCreator.createDailyReport(self.file, float(self.ui.plainTextEdit.toPlainText())))
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

    def openSettings(self):
        settingsWindow = SettingsWindow(self)
        settingsWindow.show()

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
                schedule.every().day.at(reportTime).do(lambda: ReportCreator.createDailyReport(self.file, float(self.ui.plainTextEdit.toPlainText())))
            elif schedule.get_jobs()[0].next_run.time().strftime('%H:%M') != reportTime:
                schedule.clear()
                schedule.every().day.at(reportTime).do(ReportCreator.createDailyReport, self.file)
            print(schedule.get_jobs())
            schedule.run_pending()
            print(ReportCreator.reportDone)
            if ReportCreator.reportDone:
                self.ui.reportDoneLine.setText("Отчет создан " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                self.ui.reportDoneLine.setVisible(True)
                ReportCreator.reportDone = False
            time.sleep(60)

    def threadingStart(self):
        self.stop_event = threading.Event()
        self.c_thread = threading.Thread(target=self.createDalyReportSchedule, args=(self.stop_event,))
        self.c_thread.start()

    def buttonClick(self):
        filter = "xls(*.xls *.xlsx)"
        self.file = QFileDialog.getOpenFileName(self, 'Выбрать файл', filter=filter)[0]
        self.ui.filenameTextLine.setText(os.path.basename(self.file))
        print(self.file)


class RegisterWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Регистрация пользователя')
        layout = QVBoxLayout()
        self.loginLineEdit = QLineEdit()
        self.passwordLineEdit = QLineEdit()

        button = QPushButton("Зарегистрировать")
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
            errorBox.setText("Неправильный логин или пароль")
            errorBox.exec()


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Настройки')
        layout = QVBoxLayout()

        self.databaseNameTextEdit = QTextEdit('Название БД')
        self.databaseNameTextEdit.setReadOnly(True)
        self.databaseNameTextEdit.setFixedHeight(self.databaseNameTextEdit.document().lineCount() * 30)
        self.databaseNameLineEdit = QLineEdit()

        self.userNameTextEdit = QTextEdit("Имя пользователя")
        self.userNameTextEdit.setReadOnly(True)
        self.userNameTextEdit.setFixedHeight(self.userNameTextEdit.document().lineCount() * 30)
        self.userNameLineEdit = QLineEdit()

        self.passwordTextEdit = QTextEdit("Пароль")
        self.passwordTextEdit.setReadOnly(True)
        self.passwordTextEdit.setFixedHeight(self.passwordTextEdit.document().lineCount() * 30)
        self.passwordLineEdit = QLineEdit()

        self.hostTextEdit = QTextEdit("Хост")
        self.hostTextEdit.setReadOnly(True)
        self.hostTextEdit.setFixedHeight(self.hostTextEdit.document().lineCount() * 30)
        self.hostLineEdit = QLineEdit()

        layout.addWidget(self.databaseNameTextEdit)
        layout.addWidget(self.databaseNameLineEdit)
        layout.addWidget(self.userNameTextEdit)
        layout.addWidget(self.userNameLineEdit)
        layout.addWidget(self.passwordTextEdit)
        layout.addWidget(self.passwordLineEdit)
        layout.addWidget(self.hostTextEdit)
        layout.addWidget(self.hostLineEdit)

        self.setLayout(layout)

        self.fillData()

    def closeEvent(self, event):
        print(self.databaseNameLineEdit.text())
        self.writeConfig()
        self.close()

    def writeConfig(self):
        config = readConfig()
        if self.databaseNameLineEdit.text() != '':
            config['database']['dbname'] = self.databaseNameLineEdit.text()
        if self.userNameLineEdit.text() != '':
            config['database']['user'] = self.userNameLineEdit.text()
        if self.passwordLineEdit.text() != '':
            config['database']['password'] = self.passwordLineEdit.text()
        if self.hostLineEdit.text() != '':
            config['database']['host'] = self.hostLineEdit.text()

        with open(config_path_file.CONFIG_PATH, 'w') as configfile:
            config.write(configfile)

    def fillData(self):
        config = readConfig()
        self.databaseNameLineEdit.setText(config['database']['dbname'])
        self.userNameLineEdit.setText(config['database']['user'])
        self.passwordLineEdit.setText(config['database']['password'])
        self.hostLineEdit.setText(config['database']['host'])


def readConfig():
    config = configparser.ConfigParser()
    path = config_path_file.CONFIG_PATH
    config.read(path)
    return config


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
mainWindow = MainWindow()
loginWindow = LoginWindow()
loginWindow.show()
sys.exit(app.exec())
