from typing import Iterable, List, Optional, Tuple, Union

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDateTimeEdit, QHeaderView, QMessageBox, QTableWidget,
                               QTableWidgetItem)
from mysql.connector.errors import Error

from mysql_editor.backend import Backend


class TableDataView(QTableWidget):
    def __init__(self):
        self.__backend = Backend()

        self.deleted: List[int] = []

        super().__init__(None)

        self.verticalHeader().setToolTip("Click to remove row")
        self.verticalHeader().sectionClicked.connect(self.updateDeleted)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    @Slot(int)
    def updateDeleted(self, row: int):
        deleted = row in self.deleted

        if deleted:
            self.deleted.remove(row)

        else:
            self.deleted.append(row)

        for col in range(self.columnCount()):
            try:
                self.cellWidget(row, col).setEnabled(deleted)

            except AttributeError:
                self.item(row, col).setEnabled(deleted)

    def getUnique(self) -> Tuple[str, int]:
        for col in range(self.columnCount()):
            if self.cellWidget(2, col).text() not in ("PRI", "UNI"):
                continue

            return self.horizontalHeaderItem(col).text(), col

        return self.horizontalHeaderItem(0).text(), 0

    def saveEdits(self, database: str, table: str):
        unique, uniqueCol = self.getUnique()
        _, columns = self.__backend.getTableStructure(database, table)

        rowCount = 0

        queries: List[str] = []
        parameters: List[Iterable] = []

        for row, tuple_ in enumerate(self.__backend.getData(database, table)):
            uniqueValue = self.item(row, uniqueCol).text()

            if row in self.deleted:
                queries.append(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s")
                parameters.append((uniqueValue,))

                continue

            changedValues: List[str] = []

            query = ""

            for col in range(self.columnCount()):
                cell = self.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateTimeEdit):
                        value = cell.dateTime().toString("yyyy-MM-dd hh:mm:ss")

                    else:
                        value = cell.date().toString("yyyy-MM-dd")

                if value == f"{tuple_[col]}":
                    continue

                changedValues.append(value)
                query += f"`{columns[col]}` = %s, "

            if query:
                queries.append(f"UPDATE `{database}`.`{table}` SET {query[:-2]} WHERE `{unique}` = '{uniqueValue}'")
                parameters.append(changedValues)

            rowCount += 1

        for row in range(rowCount, self.rowCount()):
            query: str = ""
            changedValues: List[str] = []

            for col in range(self.columnCount()):
                cell: QTableWidgetItem = self.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.cellWidget(row, col)

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

        self.resizeColumnsToContents()
