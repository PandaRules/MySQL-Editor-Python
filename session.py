from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QMenuBar, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem
)
from mysql.connector import connect
from mysql.connector.errors import Error

from settings import SettingsPage, SESSIONS, SESSION_FILE

from window import Window

global connection


class SessionManager(QDialog):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("Session Manager")

        self.sessions = QTreeWidget()
        self.data = {}

        for session in SESSIONS.sections():
            self.data[session] = dict(SESSIONS.items(session))

        self.sessionList = self.data.keys()

        for session in self.sessionList:
            self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

        self.sessions.setCurrentItem(None)

        self.host = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.connect = QPushButton("Connect")

        self.host.setMaxLength(15)
        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.connect.setEnabled(False)
        self.sessions.setHeaderHidden(True)

        self.connect.clicked.connect(self.open_window)
        self.sessions.currentItemChanged.connect(self.show_credentials)

        credential_layout = QGridLayout()
        credential_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credential_layout.addWidget(QLabel("Host:"), 0, 0)
        credential_layout.addWidget(self.host, 0, 1)
        credential_layout.addWidget(QLabel("User:"), 1, 0)
        credential_layout.addWidget(self.user, 1, 1)
        credential_layout.addWidget(QLabel("Password:"), 2, 0)
        credential_layout.addWidget(self.password, 2, 1)
        credential_layout.addWidget(self.connect, 3, 0, 1, 2)

        self.setLayout(QHBoxLayout())
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addWidget(self.sessions)
        self.layout().addLayout(credential_layout)

        self.layout().setMenuBar(QMenuBar())
        self.layout().menuBar().addAction("New Session", Qt.Modifier.CTRL | Qt.Key.Key_N, self.new_session)
        self.layout().menuBar().addAction("Remove Session", Qt.Modifier.CTRL | Qt.Key.Key_R, self.remove_session)
        self.layout().menuBar().addAction("Settings", Qt.Modifier.CTRL | Qt.Key.Key_I,
                                          lambda: SettingsPage(self).show())

    @Slot(QTreeWidgetItem)
    def show_credentials(self, item):
        if item is None:
            return

        data = self.data.get(item.text(0))

        self.host.setEnabled(True)
        self.user.setEnabled(True)
        self.password.setEnabled(True)
        self.connect.setEnabled(True)

        self.host.setText(data.get("host"))
        self.user.setText(data.get("user"))

    @Slot()
    def new_session(self):
        session = f"Session - {len(self.sessionList) + 1}"
        self.data[session] = {}

        self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

    @Slot()
    def remove_session(self):
        item = self.sessions.currentItem()

        if item is None:
            return

        session_name = item.text(0)
        self.sessions.setCurrentItem(None)
        self.sessions.takeTopLevelItem(self.sessions.indexOfTopLevelItem(item))

        if not self.sessions.topLevelItemCount():
            self.host.setText("")
            self.user.setText("")
            self.password.setText("")

            self.host.setEnabled(False)
            self.user.setEnabled(False)
            self.password.setEnabled(False)

        self.data.pop(session_name)
        SESSIONS.remove_section(session_name)

        with open(SESSION_FILE, "w") as file:
            SESSIONS.write(file)

    @Slot()
    def open_window(self):
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

        self.data[self.sessions.currentItem().text(0)] = {"host": host, "user": user}

        for session, credentials in self.data.items():
            SESSIONS[session] = credentials

        with open(SESSION_FILE, "w") as credentials:
            SESSIONS.write(credentials)

        self.close()

        Window(connection).show()
