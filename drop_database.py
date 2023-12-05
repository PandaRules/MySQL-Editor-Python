from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QLabel, QLayout, QMessageBox, QPushButton, QTreeWidget
from mysql.connector.cursor import MySQLCursor


class DropDatabaseWindow(QDialog):
    def __init__(self, cursor: MySQLCursor, databases: QTreeWidget):
        super().__init__()
        self.setLayout(QFormLayout())

        self.Cursor = cursor
        self.databases = databases

        self.databases_list = QComboBox()

        for i in range(self.databases.topLevelItemCount()):
            self.databases_list.addItem(self.databases.topLevelItem(i).text(0))

        self.databases_list.setCurrentIndex(-1)

        button = QPushButton("Drop")
        button.clicked.connect(self.drop)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), self.databases_list)
        self.layout().addRow(button)

    @Slot()
    def drop(self):
        database = self.databases_list.currentText()

        self.Cursor.execute(f"DROP DATABASE `{database}`;")
        self.databases_list.removeItem(self.databases_list.currentIndex())

        QMessageBox.information(self, "Success", "Successfully Dropped!")

        for i in range(self.databases.topLevelItemCount()):
            if self.databases.topLevelItem(i).text(0) != database:
                continue

            self.databases.takeTopLevelItem(i)

            break
