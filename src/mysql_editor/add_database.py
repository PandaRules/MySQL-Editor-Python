import mysql.connector.errors
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLayout, QLineEdit, QMessageBox, QPushButton, QTreeWidgetItem, QTreeWidget
)
from mysql.connector.cursor import MySQLCursor


class AddDatabaseWindow(QDialog):
    def __init__(self, cursor: MySQLCursor, databaseTree: QTreeWidget):
        super().__init__()

        self.setWindowTitle("Add database")

        self.Cursor: MySQLCursor = cursor
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

        try:
            self.Cursor.execute(f"CREATE DATABASE `{database}`;")

        except mysql.connector.errors.Error as error:
            QMessageBox.critical(self, "Error", error.msg)

            return

        self.databaseTree.blockSignals(True)
        self.databaseTree.addTopLevelItem(QTreeWidgetItem((database,)))
        self.databaseTree.blockSignals(False)

        QMessageBox.information(self, "Success", "Successfully Created")
