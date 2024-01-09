import os.path
import sys

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
SESSIONS = QSettings(SESSION_FILE, QSettings.Format.IniFormat)


class SessionManager(QDialog):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("Session Manager")

        self.sessions = QListWidget()
        self.sessionNames = []

        self.data = {}

        for group in SESSIONS.childGroups():
            self.sessionNames.append(group)

            item = QListWidgetItem(group)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            self.sessions.addItem(item)

        self.sessions.setCurrentItem(None)

        self.host = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.connectButton = QPushButton("Connect")

        self.host.setMaxLength(15)
        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.connectButton.setEnabled(False)
        self.connectButton.clicked.connect(self.openWindow)
        self.sessions.itemSelectionChanged.connect(self.showCredentials)
        self.sessions.itemDoubleClicked.connect(self.sessions.editItem)
        self.sessions.itemChanged.connect(self.renameSession)

        credential_layout = QGridLayout()
        credential_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credential_layout.addWidget(QLabel("Host:"), 0, 0)
        credential_layout.addWidget(self.host, 0, 1)
        credential_layout.addWidget(QLabel("User:"), 1, 0)
        credential_layout.addWidget(self.user, 1, 1)
        credential_layout.addWidget(QLabel("Password:"), 2, 0)
        credential_layout.addWidget(self.password, 2, 1)
        credential_layout.addWidget(self.connectButton, 3, 0, 1, 2)

        self.menubar = QMenuBar()
        self.menubar.addAction("New Session", QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_N), self.newSession)
        self.remove = self.menubar.addAction("Remove Session", QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_R),
                                             self.removeSession)

        themes = self.menubar.addMenu("Theme")

        for theme in QStyleFactory.keys():
            themes.addAction(f"{theme}", lambda theme_=theme: self.updateTheme(theme_))

        layout = QHBoxLayout()
        layout.setMenuBar(self.menubar)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self.sessions)
        layout.addLayout(credential_layout)

        self.setLayout(layout)

        self.remove.setEnabled(False)

    @staticmethod
    def updateTheme(theme: str):
        QApplication.setStyle(theme)

        SETTINGS.beginGroup("Settings")
        SETTINGS.setValue("Theme", theme)
        SETTINGS.endGroup()

    @Slot(QListWidgetItem)
    def renameSession(self, item: QListWidgetItem):
        old = self.sessionNames[self.sessions.row(item)]
        new = item.text()

        if old == new:
            return

        elif new in self.sessionNames:
            QMessageBox.critical(self, "Session already exists", "A session with that name already exists!")

            item.setText(old)

            return

        SESSIONS.beginGroup(old)
        host = SESSIONS.value("host")
        user = SESSIONS.value("user")
        SESSIONS.endGroup()

        SESSIONS.beginGroup(new)
        SESSIONS.setValue("host", host)
        SESSIONS.setValue("user", user)
        SESSIONS.endGroup()

        SESSIONS.remove(old)

        self.sessionNames[self.sessions.row(item)] = new

    @Slot()
    def newSession(self):
        sessions = sorted(
            int(split[-1]) for split in (session.split(' ') for session in SESSIONS.childGroups()) if
            "".join(split[:2]) == "Session-" and split[-1].isdigit()
        )

        count = 1

        while count in sessions:
            count += 1

        session = f"Session - {count}"

        SESSIONS.beginGroup(session)
        SESSIONS.setValue("host", "")
        SESSIONS.setValue("user", "")
        SESSIONS.endGroup()

        self.sessions.addItem(QListWidgetItem(session))

        self.sessionNames.append(session)

    @Slot()
    def removeSession(self):
        item = self.sessions.currentItem()

        if item is None:
            self.remove.setEnabled(False)

            return

        session_name = item.text()
        row = self.sessions.currentRow()
        self.sessions.setCurrentItem(None)
        self.sessions.takeItem(row)

        self.host.clear()
        self.user.clear()
        self.password.clear()

        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.connectButton.setEnabled(False)

        SESSIONS.remove(session_name)
        self.sessionNames.remove(session_name)

        self.remove.setEnabled(False)

    @Slot()
    def showCredentials(self):
        item = self.sessions.currentItem()

        if item is None:
            self.remove.setEnabled(False)

            self.host.clear()
            self.user.clear()
            self.password.clear()

            self.host.setEnabled(True)
            self.user.setEnabled(True)
            self.password.setEnabled(True)
            self.connectButton.setEnabled(True)

            return

        self.host.setEnabled(True)
        self.user.setEnabled(True)
        self.password.setEnabled(True)
        self.connectButton.setEnabled(True)

        SESSIONS.beginGroup(item.text())
        self.host.setText(SESSIONS.value("host"))
        self.user.setText(SESSIONS.value("user"))
        SESSIONS.endGroup()

        self.remove.setEnabled(True)

    @Slot()
    def openWindow(self):
        global connection

        host = self.host.text()
        user = self.user.text()
        password = self.password.text()

        try:
            connection = connect(host=host, user=user, password=password)

        except Error as error:
            QMessageBox.critical(self, "Error", error.msg)

            return

        connection.autocommit = True

        SESSIONS.beginGroup(self.sessions.currentItem().text())
        SESSIONS.setValue("host", host)
        SESSIONS.setValue("user", user)
        SESSIONS.endGroup()

        self.close()

        window = Window(connection)
        window.show()
