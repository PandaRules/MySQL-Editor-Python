import os.path
import sys
from typing import List

from PySide6.QtCore import Slot, Qt, QSettings, QKeyCombination
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout, QLineEdit, QMenuBar, QMessageBox, QPushButton, QStyleFactory,
    QApplication, QListWidget, QListWidgetItem
)
from mysql.connector import connect
from mysql.connector.errors import Error

from mysql_editor.window import Window

global connection

if sys.platform == "linux":
    CONFIG_PATH = os.path.join(os.getenv("HOME"), ".config", "MySQL Editor")

elif sys.platform == "win32":
    CONFIG_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "MySQL Editor")

else:
    CONFIG_PATH = ""

CONFIG_FILE = os.path.join(CONFIG_PATH, "config.ini")
SESSION_FILE = os.path.join(CONFIG_PATH, "sessions.ini")

SETTINGS = QSettings(CONFIG_FILE, QSettings.Format.IniFormat)


def updateTheme(theme: str):
    QApplication.setStyle(theme)

    SETTINGS.beginGroup("Settings")
    SETTINGS.setValue("Theme", theme)
    SETTINGS.endGroup()


class SessionFileHandler(object):
    __sessions = QSettings(SESSION_FILE, QSettings.Format.IniFormat)

    @classmethod
    def getSessionNames(cls) -> List[str]:
        sessionNames: List[str] = []

        for group in cls.__sessions.childGroups():
            sessionNames.append(group)

        return sessionNames

    @classmethod
    def getSessionDetails(cls, session: str) -> tuple[str, str]:
        cls.__sessions.beginGroup(session)

        host: str = cls.__sessions.value("host")
        user: str = cls.__sessions.value("user")

        cls.__sessions.endGroup()

        return host, user

    @classmethod
    def renameSession(cls, old: str, new: str) -> None:
        cls.__sessions.beginGroup(old)
        host = cls.__sessions.value("host")
        user = cls.__sessions.value("user")
        cls.__sessions.endGroup()

        cls.__sessions.beginGroup(new)
        cls.__sessions.setValue("host", host)
        cls.__sessions.setValue("user", user)
        cls.__sessions.endGroup()

        cls.__sessions.remove(old)

    @classmethod
    def updateSession(cls, session: str, host: str, user: str):
        cls.__sessions.beginGroup(session)
        cls.__sessions.setValue("host", host)
        cls.__sessions.setValue("user", user)
        cls.__sessions.endGroup()

    @classmethod
    def addSession(cls, session: str) -> None:
        cls.__sessions.beginGroup(session)
        cls.__sessions.setValue("host", "")
        cls.__sessions.setValue("user", "")
        cls.__sessions.endGroup()

    @classmethod
    def removeSession(cls, session: str) -> None:
        cls.__sessions.remove(session)


class SessionManager(QDialog):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("Session Manager")

        self.__sessions = QListWidget()
        self.__sessionNames: List[str] = SessionFileHandler.getSessionNames()

        self.__data = {}

        for group in self.__sessionNames:
            item = QListWidgetItem(group)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            self.__sessions.addItem(item)

        self.__sessions.setCurrentItem(None)

        self.__host = QLineEdit()
        self.__user = QLineEdit()
        self.__password = QLineEdit()
        self.__connect = QPushButton("Connect")

        self.__host.setMaxLength(15)
        self.__host.setEnabled(False)
        self.__user.setEnabled(False)
        self.__password.setEnabled(False)
        self.__password.setEchoMode(QLineEdit.EchoMode.Password)
        self.__password.textChanged.connect(lambda text: self.__connect.setEnabled(len(text) != 0))
        self.__connect.setEnabled(False)
        self.__connect.clicked.connect(self.__openWindow)
        self.__sessions.itemSelectionChanged.connect(self.__showCredentials)
        self.__sessions.itemDoubleClicked.connect(self.__sessions.editItem)
        self.__sessions.itemChanged.connect(self.__renameSession)

        credential_layout = QGridLayout()
        credential_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credential_layout.addWidget(QLabel("Host:"), 0, 0)
        credential_layout.addWidget(self.__host, 0, 1)
        credential_layout.addWidget(QLabel("User:"), 1, 0)
        credential_layout.addWidget(self.__user, 1, 1)
        credential_layout.addWidget(QLabel("Password:"), 2, 0)
        credential_layout.addWidget(self.__password, 2, 1)
        credential_layout.addWidget(self.__connect, 3, 0, 1, 2)

        self.__menubar = QMenuBar()
        self.__menubar.addAction("New Session", QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_N), self.__newSession)
        self.__remove = self.__menubar.addAction("Remove Session", QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_R),
                                                 self.__removeSession)

        themes = self.__menubar.addMenu("Theme")

        for theme in QStyleFactory.keys():
            themes.addAction(f"{theme}", lambda theme_=theme: updateTheme(theme_))

        layout = QHBoxLayout()
        layout.setMenuBar(self.__menubar)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self.__sessions)
        layout.addLayout(credential_layout)

        self.setLayout(layout)

        self.__remove.setEnabled(False)

    @Slot(QListWidgetItem)
    def __renameSession(self, item: QListWidgetItem):
        old = self.__sessionNames[self.__sessions.row(item)]
        new = item.text()

        if old == new:
            return

        elif new in self.__sessionNames:
            QMessageBox.critical(self, "Session already exists", "A session with that name already exists!")

            item.setText(old)

            return

        SessionFileHandler.renameSession(old, new)

        self.__sessionNames[self.__sessions.row(item)] = new

    @Slot()
    def __newSession(self):
        sessions = sorted(
            int(split[-1]) for split in (session.split(' ') for session in SessionFileHandler.getSessionNames()) if
            "".join(split[:2]) == "Session-" and split[-1].isdigit()
        )

        count = 1

        while count in sessions:
            count += 1

        session = f"Session - {count}"

        SessionFileHandler.addSession(session)

        self.__sessions.addItem(QListWidgetItem(session))

        self.__sessionNames.append(session)

    @Slot()
    def __removeSession(self):
        item = self.__sessions.currentItem()

        if item is None:
            self.__remove.setEnabled(False)

            return

        session = item.text()
        row = self.__sessions.currentRow()
        self.__sessions.setCurrentItem(None)
        self.__sessions.takeItem(row)

        self.__host.clear()
        self.__user.clear()
        self.__password.clear()

        self.__host.setEnabled(False)
        self.__user.setEnabled(False)
        self.__password.setEnabled(False)
        self.__connect.setEnabled(False)

        SessionFileHandler.removeSession(session)
        self.__sessionNames.remove(session)

        self.__remove.setEnabled(False)

    @Slot()
    def __showCredentials(self):
        item = self.__sessions.currentItem()

        if item is None:
            self.__remove.setEnabled(False)

            self.__host.clear()
            self.__user.clear()
            self.__password.clear()

            self.__host.setEnabled(True)
            self.__user.setEnabled(True)
            self.__password.setEnabled(True)

            return

        self.__host.setEnabled(True)
        self.__user.setEnabled(True)
        self.__password.setEnabled(True)
        self.__connect.setEnabled(len(self.__password.text()) != 0)

        host, user = SessionFileHandler.getSessionDetails(item.text())

        self.__host.setText(host)
        self.__user.setText(user)

        self.__remove.setEnabled(True)

    @Slot()
    def __openWindow(self):
        global connection

        host = self.__host.text()
        user = self.__user.text()
        password = self.__password.text()

        try:
            connection = connect(host=host, user=user, password=password)

        except Error as error:
            QMessageBox.critical(self, "Error", error.msg)

            return

        connection.autocommit = True

        SessionFileHandler.updateSession(self.__sessions.currentItem().text(), host, user)

        self.close()

        window = Window(connection)
        window.show()
