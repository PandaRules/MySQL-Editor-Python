from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox, QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from mysql_editor.files import File


class QueryTabViewer(QTabWidget):
    def __init__(self, parent: Optional[QWidget]):
        super().__init__(parent)

        addButton = QPushButton("+")
        addButton.clicked.connect(self.__addQueryTab)

        self.setCornerWidget(addButton)
        self.addTab(QueryTab(self), "Tab - 1")

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.__removeQueryTab)

    @Slot()
    def __addQueryTab(self):
        tabs = sorted(
            int(split[-1]) for split in
            (self.tabText(num).replace('&', '').split(" ") for num in range(self.count()))
            if "".join(split[:2]) == "Tab-" and split[-1].isdigit()
        )

        count = 1

        while count in tabs:
            count += 1

        self.addTab(QueryTab(self), f"Tab - {count}")

    @Slot(int)
    def __removeQueryTab(self, index):
        if self.count() != 1:
            self.removeTab(index)

    def checkSave(self) -> bool:
        for index in range(self.count()):
            if self.tabText(index)[:2] != "* ":
                continue

            option = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"You have unsaved changes in {self.tabText(index)[2:]}. Would you like to save them?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if option == QMessageBox.StandardButton.Cancel:
                return False

            if option == QMessageBox.StandardButton.Save:
                self.widget(index).save()

        return True


class QueryTab(QWidget):
    def __init__(self, tabs: QTabWidget):
        super().__init__()

        self.tabs = tabs

        self.queryBox = QTextEdit()
        self.results = QTabWidget()

        self.file: Optional[File] = None

        self.queryBox.textChanged.connect(self.checkIfEdited)

        layout = QVBoxLayout()
        layout.addWidget(self.queryBox)
        layout.addWidget(self.results)
        self.setLayout(layout)

        self.results.hide()

    @Slot()
    def checkIfEdited(self):
        if self.file is None:
            return

        contents = self.queryBox.toPlainText()

        index = self.tabs.currentIndex()

        if contents != self.file.contents:
            self.tabs.setTabText(index, f"* {self.file.name}")

        elif self.tabs.tabText(index)[:2] == "* ":
            self.tabs.setTabText(index, self.file.name)

    @Slot()
    def openFile(self):
        fileName: str = QFileDialog.getOpenFileName(self, "Open File", "", "SQL Query File (*.sql)")[0]

        if not fileName or fileName[-4:] != ".sql":
            return

        if self.file is None:
            self.file = File()

        self.file.open(fileName, "r+")
        self.queryBox.setText(self.file.contents)

        self.tabs.setTabText(self.tabs.currentIndex(), fileName)

    @Slot()
    def saveFile(self):
        if self.file is None:
            fileName: str = QFileDialog.getSaveFileName(self, "Save File", "", "SQL Query File (*.sql)")[0]

            if not fileName or fileName[-4:] != ".sql":
                return

            self.file = File()

            self.file.open(fileName, "w+")

        self.file.save(self.queryBox.toPlainText())

        self.tabs.setTabText(self.tabs.currentIndex(), self.file.name)

    @Slot()
    def saveFileAs(self):
        fileName: str = QFileDialog.getSaveFileName(self, "Save File As", "", "SQL Query File (*.sql)")[0]

        if not fileName or fileName[-4:] != ".sql":
            return

        if self.file is None:
            self.file = File()

        self.file.open(fileName, "w+")
        self.file.save(self.queryBox.toPlainText())

        self.tabs.setTabText(self.tabs.currentIndex(), fileName)
