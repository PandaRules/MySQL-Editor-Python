from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QLineEdit, QMenuBar, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem
)
from mysql.connector import connect
from mysql.connector.errors import Error

from mysql_editor.settings import SettingsPage, SESSIONS, SESSION_FILE
from mysql_editor.window import Window

global connection


class SessionManager(QDialog):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("Session Manager")

        self.sessions = QTreeWidget()
        self.data = {}

        for session in SESSIONS.sections():
            self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

        self.sessions.setCurrentItem(None)

        self.session = QLineEdit()
        self.host = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.connect = QPushButton("Connect")

        self.session.setEnabled(False)
        self.host.setMaxLength(15)
        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.connect.setEnabled(False)
        self.sessions.setHeaderHidden(True)

        self.session.textEdited.connect(self.rename_session)
        self.connect.clicked.connect(self.open_window)
        self.sessions.itemSelectionChanged.connect(self.show_credentials)

        credential_layout = QGridLayout()
        credential_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credential_layout.addWidget(self.session, 0, 0, 1, 2)
        credential_layout.addWidget(QLabel("Host:"), 1, 0)
        credential_layout.addWidget(self.host, 1, 1)
        credential_layout.addWidget(QLabel("User:"), 2, 0)
        credential_layout.addWidget(self.user, 2, 1)
        credential_layout.addWidget(QLabel("Password:"), 3, 0)
        credential_layout.addWidget(self.password, 3, 1)
        credential_layout.addWidget(self.connect, 4, 0, 1, 2)

        layout = QHBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self.sessions)
        layout.addLayout(credential_layout)

        self.menubar = QMenuBar()
        self.menubar.addAction("New Session", Qt.Modifier.CTRL | Qt.Key.Key_N, self.new_session)
        self.remove = self.menubar.addAction("Remove Session", Qt.Modifier.CTRL | Qt.Key.Key_R, self.remove_session)
        self.menubar.addAction("Settings", Qt.Modifier.CTRL | Qt.Key.Key_I, lambda: SettingsPage(self).show())
        layout.setMenuBar(self.menubar)

        self.setLayout(layout)

        self.remove.setEnabled(False)

    @Slot(str)
    def rename_session(self, text: str):
        current_name = self.sessions.currentItem().text(0)

        self.sessions.currentItem().setText(0, text)

        SESSIONS[text] = SESSIONS[current_name]
        SESSIONS.remove_section(current_name)

    @Slot()
    def show_credentials(self):
        item = self.sessions.currentItem()

        if item is None:
            self.remove.setEnabled(False)

            return

        data = SESSIONS[item.text(0)]

        self.session.setEnabled(True)
        self.host.setEnabled(True)
        self.user.setEnabled(True)
        self.password.setEnabled(True)
        self.connect.setEnabled(True)

        self.session.setText(item.text(0))
        self.host.setText(data.get("host"))
        self.user.setText(data.get("user"))

        self.remove.setEnabled(True)

    @Slot()
    def new_session(self):
        sessions = []

        for session in SESSIONS.sections():
            split = session.split(' ')[-1]

            if not split.isdigit():
                continue

            sessions.append(int(split))

        sessions.sort()

        count = 1

        while count in sessions:
            count += 1

        session = f"Session - {count}"
        SESSIONS.add_section(session)

        self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

    @Slot()
    def remove_session(self):
        item = self.sessions.currentItem()

        if item is None:
            self.remove.setEnabled(False)

            return

        session_name = item.text(0)
        self.sessions.setCurrentItem(None)
        self.sessions.takeTopLevelItem(self.sessions.indexOfTopLevelItem(item))

        self.session.clear()
        self.host.clear()
        self.user.clear()
        self.password.clear()

        self.session.setEnabled(False)
        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.connect.setEnabled(False)

        SESSIONS.remove_section(session_name)

        with open(SESSION_FILE, "w") as file:
            SESSIONS.write(file)

        self.remove.setEnabled(False)

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

        SESSIONS[self.session.text()] = {"host": host, "user": user}

        with open(SESSION_FILE, "w") as credentials:
            SESSIONS.write(credentials)

        self.close()

        window = Window(connection)
        window.show()
