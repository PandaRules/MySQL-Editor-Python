from PySide6.QtWidgets import QTableWidget, QHeaderView


class TableStructureView(QTableWidget):
    def __init__(self):
        super().__init__(None)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
