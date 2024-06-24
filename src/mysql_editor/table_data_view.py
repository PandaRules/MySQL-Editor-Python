from typing import Iterable, List, Optional, Union

from PySide6.QtCore import QDate, QDateTime, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDateEdit, QDateTimeEdit, QHeaderView, QMenuBar,
                               QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from mysql.connector.errors import Error

from mysql_editor.backend import Backend


class TableDataView(QWidget):
    def __init__(self):
        self.__backend = Backend()

        self.deleted: List[int] = []

        super().__init__(None)

        self.__database: str = ""
        self.__table: str = ""

        self.__data = QTableWidget(self)

        self.__data.verticalHeader().setToolTip("Click to remove row")
        self.__data.verticalHeader().sectionClicked.connect(self.updateDeleted)

        self.__data.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        menubar = QMenuBar()
        menubar.addAction("Add New Entry", lambda: self.__data.setRowCount(self.__data.rowCount() + 1))
        menubar.addAction("Save Changes", lambda: self.saveEdits(self.__database, self.__table))
        menubar.addAction("Cancel Changes", lambda: self.setTable(self.__database, self.__table))

        self.__tableActions: List[QAction] = menubar.actions()

        self.setActionsClickable(False)

        layout = QVBoxLayout(self)
        layout.setMenuBar(menubar)
        layout.addWidget(self.__data)

    def setTable(self, database: str, table: str) -> None:
        data, columns = self.__backend.getData(database, table)
        structure, _ = self.__backend.getTableStructure(database, table)

        self.__database = database
        self.__table = table

        self.__data.clear()
        self.__data.setRowCount(len(data))
        self.__data.setColumnCount(len(columns))
        self.__data.setHorizontalHeaderLabels(columns)

        for row, tuple_ in enumerate(data):
            self.__data.setRowHidden(row, False)

            for col, value in enumerate(tuple_):
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                if structure[col][1][:4] == "enum":
                    options = QComboBox()
                    options.addItems(eval(structure[col][1][4:]))
                    options.setCurrentText(f"{value}")

                    self.__data.setCellWidget(row, col, options)

                elif structure[col][1] == "date":
                    currentDate = QDate.fromString(f"{value}", "yyyy-MM-dd")

                    date = QDateEdit()
                    date.setDisplayFormat("yyyy-MM-dd")
                    date.setCalendarPopup(True)

                    if currentDate < date.minimumDate():
                        date.setMinimumDate(currentDate)

                    elif currentDate > date.maximumDate():
                        date.setMaximumDate(currentDate)

                    if structure[col][2] != "":
                        default = QDate.fromString(f"{structure[col][2]}", "yyyy-MM-dd")

                        if default < date.minimumDate():
                            date.setMinimumDate(default)

                        elif default > date.maximumDate():
                            date.setMaximumDate(default)

                    date.setDate(currentDate)

                    self.__data.setCellWidget(row, col, date)

                elif structure[col][1] == "datetime":
                    currentDate = QDateTime.fromString(f"{value}", "yyyy-MM-dd hh:mm:ss")

                    date = QDateTimeEdit()
                    date.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
                    date.setCalendarPopup(True)

                    if currentDate < date.minimumDate():
                        date.setMinimumDateTime(currentDate)

                    elif currentDate > date.maximumDate():
                        date.setMaximumDateTime(currentDate)

                    if structure[col][2] != "":
                        default = QDateTime.fromString(f"{structure[col][2]}", "yyyy-MM-dd hh:mm:ss")

                        if default < date.minimumDate():
                            date.setMinimumDateTime(default)

                        elif default > date.maximumDate():
                            date.setMaximumDateTime(default)

                    date.setDateTime(currentDate)

                    self.__data.setCellWidget(row, col, date)

                else:
                    self.__data.setItem(row, col, QTableWidgetItem(f"{value}"))

        self.setActionsClickable(True)

        if database in ("information_schema", "mysql", "sys", "performance"):
            self.__data.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.__data.verticalHeader().setToolTip("")
            self.__data.verticalHeader().sectionClicked.disconnect(self.updateDeleted)

        else:
            self.__data.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked |
                QAbstractItemView.EditTrigger.EditKeyPressed |
                QAbstractItemView.EditTrigger.AnyKeyPressed
            )
            self.__data.verticalHeader().setToolTip("Click to remove row")
            self.__data.verticalHeader().sectionClicked.connect(self.updateDeleted)

    def clearData(self) -> None:
        self.__data.setRowCount(0)
        self.__data.setColumnCount(0)

    def setActionsClickable(self, clickable: bool) -> None:
        for action in self.__tableActions:
            action.setEnabled(clickable)

    @Slot(int)
    def updateDeleted(self, row: int):
        deleted = row in self.deleted

        if deleted:
            self.deleted.remove(row)

        else:
            self.deleted.append(row)

        for col in range(self.__data.columnCount()):
            try:
                self.__data.cellWidget(row, col).setEnabled(deleted)

            except AttributeError:
                self.__data.item(row, col).setEnabled(deleted)

    def saveEdits(self, database: str, table: str):
        structure, _ = self.__backend.getTableStructure(database, table)

        for row, tuple_ in enumerate(structure):
            if tuple_[3] not in ("PRI", "UNI"):
                continue

            unique, uniqueCol = tuple_[0], row

            break

        else:
            unique, uniqueCol = structure[0][0], 0

        rowCount = 0

        queries: List[str] = []
        parameters: List[Iterable] = []

        data, columns = self.__backend.getData(database, table)

        for row, tuple_ in enumerate(data):
            uniqueValue = self.__data.item(row, uniqueCol).text()

            if row in self.deleted:
                queries.append(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s")
                parameters.append((uniqueValue,))

                continue

            changedValues: List[str] = []

            query: List[str] = []

            for col in range(self.__data.columnCount()):
                cell = self.__data.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.__data.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateTimeEdit):
                        value = cell.dateTime().toString("yyyy-MM-dd hh:mm:ss")

                    else:
                        value = cell.date().toString("yyyy-MM-dd")

                if value == f"{tuple_[col]}":
                    continue

                changedValues.append(value)
                query.append(f"`{columns[col]}` = %s")

            if query:
                queries.append(
                    f"UPDATE `{database}`.`{table}` SET {', '.join(query)} WHERE `{unique}` = '{uniqueValue}'")
                parameters.append(changedValues)

            rowCount += 1

        for row in range(rowCount, self.__data.rowCount()):
            query: str = ""
            changedValues: List[str] = []

            for col in range(self.__data.columnCount()):
                cell: QTableWidgetItem = self.__data.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.__data.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateTimeEdit):
                        value = cell.dateTime().toString("yyyy-MM-dd hh:mm:ss")

                    else:
                        value = cell.date().toString("yyyy-MM-dd")

                changedValues.append(value)
                query += "%s, "

            queries.append(f"INSERT INTO `{database}`.`{table}` VALUES ({query[:-2]});")
            parameters.append(changedValues)

        error: Optional[Error] = self.__backend.executeQueries(queries, parameters)

        if error is not None:
            QMessageBox.critical(self, "Error", error.msg)

            return

        QMessageBox.information(self, "Success", "Successfully Executed")

        self.__data.resizeColumnsToContents()
