import mysql.connector.errors
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLayout, QLineEdit, QMessageBox, QPushButton, QTreeWidgetItem, QTreeWidget
)
from mysql.connector.cursor import MySQLCursor


class AddDatabaseWindow(QDialog):
    def __init__(self, cursor: MySQLCursor, databases: QTreeWidget):
        super().__init__()

        self.setWindowTitle("Add database")

        self.Cursor = cursor
        self.databases = databases

        entry = QLineEdit()
        button = QPushButton("Add")
        button.clicked.connect(lambda: self.add(entry.text()))

        layout = QFormLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addRow(QLabel("Database:"), entry)
        layout.addRow(button)
        self.setLayout(layout)

    def add(self, database):
        try:
            self.Cursor.execute(f"CREATE DATABASE `{database}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error", e.msg)

            return

        self.databases.blockSignals(True)

        self.databases.insertTopLevelItem(self.databases.topLevelItemCount() - 1, QTreeWidgetItem((database,)))

        self.databases.blockSignals(False)

        QMessageBox.information(self, "Success", "Successfully Created")
