import os.path
import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from mysql_editor.session import SessionManager
from mysql_editor.settings import SUPPORTED, SETTINGS, SESSIONS, CONFIG_PATH, CONFIG_FILE, SESSION_FILE

app = QApplication()

if not SUPPORTED:
    QMessageBox.critical(QWidget(), "Unsupported", "Only Windows and Linux are supported!")

    sys.exit(app.exec())

if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)

SETTINGS.read(CONFIG_FILE)
SESSIONS.read(SESSION_FILE)

if "Settings" in SETTINGS:
    app.setStyle(SETTINGS["Settings"]["Theme"])

SessionManager().show()

sys.exit(app.exec())
