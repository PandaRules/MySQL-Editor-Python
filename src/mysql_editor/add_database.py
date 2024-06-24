from typing import Optional

from mysql.connector.errors import Error
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QDialog, QFormLayout, QLabel, QLayout, QLineEdit, QMessageBox, QPushButton, QTreeWidget,
                               QTreeWidgetItem)

from mysql_editor.backend import Backend


class AddDatabaseWindow(QDialog):
    def __init__(self, databaseTree: QTreeWidget):
        super().__init__()

        self.setWindowTitle("Add database")

        self.__backend = Backend()
        self.databaseTree: QTreeWidget = databaseTree

        self.entry = QLineEdit()
        button = QPushButton("Add")
        button.clicked.connect(self.add)

        layout = QFormLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addRow(QLabel("Database:"), self.entry)
        layout.addRow(button)
        self.setLayout(layout)

    @Slot()
    def add(self):
        database: str = self.entry.text()

        error: Optional[Error] = self.__backend.addDatabase(database)

        if error is not None:
            QMessageBox.critical(self, "Error", error.msg)

            return

        self.databaseTree.blockSignals(True)
        self.databaseTree.addTopLevelItem(QTreeWidgetItem((database,)))
        self.databaseTree.blockSignals(False)

        QMessageBox.information(self, "Success", "Successfully Created")
