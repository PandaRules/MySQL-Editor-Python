from typing import List, Tuple

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QTableWidget, QHeaderView


class TableDataView(QTableWidget):
    def __init__(self):
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
