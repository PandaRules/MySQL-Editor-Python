import os.path
import sys

from PySide6.QtWidgets import QApplication

from mysql_editor.session import SessionManager
from mysql_editor.settings import SETTINGS, SESSIONS, CONFIG_PATH, CONFIG_FILE, SESSION_FILE

app = QApplication()

if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)

SETTINGS.read(CONFIG_FILE)
SESSIONS.read(SESSION_FILE)

if "Settings" in SETTINGS:
    app.setStyle(SETTINGS["Settings"]["Theme"])

SessionManager().show()

sys.exit(app.exec())
