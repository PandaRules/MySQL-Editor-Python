from PySide6.QtCore import Slot
from PySide6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget, QFileDialog

from mysql_editor.files import File


class QueryTab(QWidget):
    def __init__(self, tabs: QTabWidget):
        super().__init__()

        self.tabs = tabs

        self.queryBox = QTextEdit()
        self.results = QTabWidget()

        self.file: File | None = None

        self.queryBox.textChanged.connect(self.check)

        layout = QVBoxLayout()
        layout.addWidget(self.queryBox)
        layout.addWidget(self.results)
        self.setLayout(layout)

        self.results.hide()

    @Slot()
    def check(self):
        if self.file is None:
            return

        contents = self.queryBox.toPlainText()

        index = self.tabs.currentIndex()

        if contents != self.file.contents:
            self.tabs.setTabText(index, "* " + self.file.name)

        elif self.tabs.tabText(index)[:2] == "* ":
            self.tabs.setTabText(index, self.file.name)

    @Slot()
    def open_file(self):
        file_name = QFileDialog.getOpenFileName(self, "Open File", "", "SQL Query File (*.sql)")[0]

        if not file_name or file_name[-4:] != ".sql":
            return

        if self.file is None:
            self.file = File()

        self.file.open(file_name, "r+")
        self.queryBox.setText(self.file.contents)

        self.tabs.setTabText(self.tabs.currentIndex(), file_name)

    @Slot()
    def save_file(self):
        if self.file is None:
            file_name = QFileDialog.getSaveFileName(self, "Save File As", "", "SQL Query File (*.sql)")[0]

            if not file_name or file_name[-4:] != ".sql":
                return

            if self.file is None:
                self.file = File()

            self.file.open(file_name, "w+")

        self.file.save(self.queryBox.toPlainText())

        self.tabs.setTabText(self.tabs.currentIndex(), self.file.name)

    @Slot()
    def save_file_as(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File", "", "SQL Query File (*.sql)")[0]

        if not file_name or file_name[-4:] != ".sql":
            return

        if self.file is None:
            self.file = File()

        self.file.open(file_name, "w+")
        self.file.save(self.queryBox.toPlainText())

        self.tabs.setTabText(self.tabs.currentIndex(), file_name)
