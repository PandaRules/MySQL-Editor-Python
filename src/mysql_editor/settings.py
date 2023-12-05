import os.path
import sys
from configparser import ConfigParser

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QLabel, QLayout, QMessageBox, QPushButton, QStyleFactory, QApplication
)

if sys.platform == "linux":
    CONFIG_PATH = os.path.join(os.getenv("HOME"), ".config", "MySQL Editor")

elif sys.platform == "win32":
    CONFIG_PATH = os.path.join(os.getenv("LOCALAPPDATA"), "MySQL Editor")

else:
    CONFIG_PATH = ""

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

        layout = QFormLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addRow(QLabel("Theme:"), self.theme)
        layout.addRow(update_button)
        self.setLayout(layout)

        if "Settings" in SETTINGS:
            self.theme.setCurrentText(SETTINGS["Settings"]["Theme"])
            
        self.theme.currentTextChanged.connect(lambda theme: QApplication.setStyle(theme))

    @Slot()
    def save_settings(self):
        SETTINGS["Settings"] = {"Theme": self.theme.currentText()}

        with open(CONFIG_FILE, "w") as file:
            SETTINGS.write(file)

        QMessageBox.information(self, "Success", "Changes will take place once you restart the application")
