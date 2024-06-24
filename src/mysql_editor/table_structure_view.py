from PySide6.QtWidgets import QLabel, QTableWidget, QHeaderView, QTableWidgetItem

from mysql_editor.backend import Backend


class TableStructureView(QTableWidget):
    def __init__(self):
        super().__init__(None)

        self.__backend = Backend()

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def setTable(self, database: str, table: str) -> None:
        structure, columns = self.__backend.getTableStructure(database, table)

        self.clear()
        self.setColumnCount(len(structure))
        self.setRowCount(len(columns) - 1)
        self.setVerticalHeaderLabels(columns[1:])

        for row, tuple_ in enumerate(structure):
            for col, value in enumerate(tuple_[1:]):
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                self.setCellWidget(col, row, QLabel(value))

            self.setHorizontalHeaderItem(row, QTableWidgetItem(tuple_[0]))

    def clearData(self) -> None:
        self.setRowCount(0)
        self.setColumnCount(0)
