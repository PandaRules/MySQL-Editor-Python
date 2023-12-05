from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QLabel, QLayout, QMessageBox, QPushButton, QTreeWidget
from mysql.connector.cursor import MySQLCursor


class DropTableWindow(QDialog):
    def __init__(self, cursor: MySQLCursor, databases: QTreeWidget):
        super().__init__()
        self.setLayout(QFormLayout())

        self.Cursor = cursor
        self.databases = databases

        self.Cursor.execute("SHOW DATABASES;")

        self.databases_list = QComboBox()

        for i in range(self.databases.topLevelItemCount()):
            self.databases_list.addItem(self.databases.topLevelItem(i).text(0))

        self.databases_list.setCurrentIndex(-1)
        self.databases_list.currentTextChanged.connect(self.show_tables)

        self.tables = QComboBox()

        button = QPushButton("Drop")
        button.clicked.connect(lambda: self.drop(self.databases_list.currentText(), self.tables.currentText()))

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), self.databases_list)
        self.layout().addRow(QLabel("Table:"), self.tables)
        self.layout().addRow(button)

    @Slot(str)
    def show_tables(self, database):
        for i in range(self.databases.topLevelItemCount()):
            if self.databases.topLevelItem(i).text(0) != database:
                continue

            for j in range(self.databases.topLevelItem(i).childCount()):
                self.tables.addItem(self.databases.topLevelItem(i).child(j).text(0))

            break

        self.tables.setCurrentIndex(-1)

    def drop(self, database, table):
        self.Cursor.execute(f"DROP TABLE `{database}`.`{table}`;")

        QMessageBox.information(self, "Success", "Successfully Dropped!")

        for i in range(self.databases.topLevelItemCount()):
            if self.databases.topLevelItem(i).text(0) != database:
                continue

            for j in range(self.databases.topLevelItem(i).childCount()):
                if self.databases.topLevelItem(i).child(j).text(0) != table:
                    continue

                self.databases.topLevelItem(i).takeChild(j)

                break

            else:
                continue

            break
