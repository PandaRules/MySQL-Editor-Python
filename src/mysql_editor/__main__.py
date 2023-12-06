import os.path
import sys

from PySide6.QtWidgets import QApplication
from mysql_editor.session import SessionManager, SETTINGS, CONFIG_PATH

app = QApplication()

if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)

if "Settings" in SETTINGS:
    app.setStyle(SETTINGS["Settings"]["Theme"])

session_manager = SessionManager()
session_manager.show()

sys.exit(app.exec())
