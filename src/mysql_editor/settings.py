import sys
import os
import os.path
from configparser import ConfigParser

from PySide6.QtCore import Slot, QEventLoop
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QLabel, QLayout,
    QMessageBox, QProgressBar, QPushButton, QStyleFactory, QVBoxLayout, QApplication
)
from requests import get
from requests.exceptions import ConnectionError

if sys.platform == "linux":
    EXECUTABLE_NAME = "MySQL Editor.bin"
    CONFIGURATOR_NAME = "MySQL Editor Configurator.bin"
    EXECUTABLE_PATH = os.path.join(os.getenv("HOME"), ".local", "share", "MySQL Editor")
    CONFIG_PATH = os.path.join(os.getenv("HOME"), ".config", "MySQL Editor")

    SUPPORTED = True

elif sys.platform == "win32":
    EXECUTABLE_NAME = "MySQL Editor.exe"
    CONFIGURATOR_NAME = "MySQL Editor Configurator.exe"
    EXECUTABLE_PATH = os.path.join(os.getenv("APPDATA"), "MySQL Editor")
    CONFIG_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "MySQL Editor")

    SUPPORTED = True

else:
    EXECUTABLE_NAME = ""
    CONFIGURATOR_NAME = ""
    EXECUTABLE_PATH = ""
    CONFIG_PATH = ""

    SUPPORTED = False

cwd = os.getcwd()

if EXECUTABLE_PATH != cwd:
    EXECUTABLE_PATH = cwd
    CONFIG_PATH = cwd

EXECUTABLE_FILE = os.path.join(EXECUTABLE_PATH, EXECUTABLE_NAME)
CONFIGURATOR_FILE = os.path.join(EXECUTABLE_PATH, CONFIGURATOR_NAME)

SETTINGS = ConfigParser()
SESSIONS = ConfigParser()

CONFIG_FILE = os.path.join(CONFIG_PATH, "config.ini")
SESSION_FILE = os.path.join(CONFIG_PATH, "sessions.ini")


class SettingsPage(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Settings")

        self.theme = QComboBox()
        self.theme.addItems(QStyleFactory().keys())

        update_button = QPushButton("Update")
        update_button.clicked.connect(self.save_settings)

        check_updates = QPushButton("Check for updates")
        check_updates.clicked.connect(self.update_app)

        layout = QFormLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addRow(QLabel("Theme:"), self.theme)
        layout.addRow(update_button)
        layout.addRow(QLabel("Update Checker"))
        layout.addRow(check_updates)
        self.setLayout(layout)

        self.theme.setCurrentText(QApplication.style().name())
        self.theme.currentTextChanged.connect(lambda theme: QApplication.setStyle(theme))

    @Slot()
    def save_settings(self):
        SETTINGS["Settings"] = {"Theme": self.theme.currentText()}

        with open(CONFIG_FILE, "w") as file:
            SETTINGS.write(file)

        QMessageBox.information(self, "Success", "Changes will take place once you restart the application")

    @Slot()
    def update_app(self):
        updater = QDialog(self)
        updater.setWindowTitle("MySql Editor Updater")

        status = QLabel()

        updater.setLayout(QVBoxLayout())
        updater.layout().addWidget(status)

        if not os.path.isdir(EXECUTABLE_PATH):
            os.mkdir(EXECUTABLE_PATH)

        try:
            request = get("https://api.github.com/repos/PandaRules/MySQL-Editor-Python/releases/latest")

        except ConnectionError:
            QMessageBox.critical(self, "Error", "No internet connection")

            return

        release = request.json()

        if "Update" in SETTINGS:
            version = SETTINGS["Update"]["version"]

        else:
            version = "v0.0.0"

        if version == release["tag_name"]:
            QMessageBox.information(self, "Up to date", "No update found")

            return

        choice = QMessageBox.question(
            self,
            "MySQL Editor Updater",
            "An update is available.\nWould you like to update?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if choice == QMessageBox.StandardButton.No:
            return

        progress_bar = QProgressBar()
        updater.layout().addWidget(progress_bar)

        flag = False

        for asset in release["assets"]:
            name = asset["name"].replace('-', ' ')

            if name == EXECUTABLE_NAME:
                file = EXECUTABLE_FILE

            elif name == CONFIGURATOR_NAME:
                file = CONFIGURATOR_FILE

            else:
                continue

            flag = True

            status.setText(f"Updating {name[:-4]}... please wait")
            status.repaint()

            QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

            while True:
                try:
                    request = get(asset["url"], stream=True, headers={"Accept": "application/octet-stream"})

                    break

                except ConnectionError:
                    continue

            request.raw.decode_content = True

            with open(file, "wb") as executable:
                total_size = asset["size"]
                size = 0

                for chunk in request.iter_content(1024):
                    size += executable.write(chunk)
                    progress_bar.setValue(size * 100 / total_size)

        if flag:
            SETTINGS["Update"] = {"version": release["tag_name"]}

            with open(CONFIG_FILE, "w") as file:
                SETTINGS.write(file)

            status.setText("Successfully Updated!\nRestart for changes to take effect.")

        else:
            status.setText("No suitable update file found")

        progress_bar.hide()
