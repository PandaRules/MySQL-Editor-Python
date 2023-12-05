from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLayout, QLineEdit, QMessageBox, QPushButton, QTreeWidgetItem, QTreeWidget
)
from mysql.connector.cursor import MySQLCursor


class AddDatabaseWindow(QDialog):
    def __init__(self, cursor: MySQLCursor, databases: QTreeWidget):
        super().__init__()

        self.setWindowTitle("Add database")
        self.setLayout(QFormLayout())

        self.Cursor = cursor
        self.databases = databases

        entry = QLineEdit()
        button = QPushButton("Add")
        button.clicked.connect(lambda: self.add(entry.text()))

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), entry)
        self.layout().addRow(button)

    def add(self, database):
        self.Cursor.execute(f"SHOW DATABASES LIKE '{database}';")

        if self.Cursor.fetchone():
            QMessageBox.information(self, "Error", "Database already exists")

            return

        self.Cursor.execute(f"CREATE DATABASE `{database}`;")

        self.databases.addTopLevelItem(QTreeWidgetItem((database,)))

        QMessageBox.information(self, "Success", "Successfully Created")
