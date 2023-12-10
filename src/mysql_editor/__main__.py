import sys

from PySide6.QtWidgets import QApplication

from mysql_editor.session import SessionManager, SETTINGS

app = QApplication()

SETTINGS.beginGroup("Settings")
QApplication.setStyle(SETTINGS.value("Theme"))
SETTINGS.endGroup()

session_manager = SessionManager()
session_manager.show()

sys.exit(app.exec())
