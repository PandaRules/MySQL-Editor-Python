from typing import Any, List, Optional, Tuple, Union

from PySide6.QtCore import QKeyCombination, QPoint, Qt, Slot
from PySide6.QtWidgets import (QHeaderView, QLabel, QMainWindow, QMenu, QMessageBox, QSplitter, QTabWidget,
                               QTableWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from mysql.connector import MySQLConnection
from mysql.connector.errors import Error

from mysql_editor.add_database import AddDatabaseWindow
from mysql_editor.backend import Backend
from mysql_editor.query import QueryTab, QueryTabViewer
from mysql_editor.table_data_view import TableDataView
from mysql_editor.table_structure_view import TableStructureView


class WindowUI(QMainWindow):
    def __init__(self, connection: MySQLConnection):
        super().__init__(None)

        self.setWindowTitle("MySQL Editor")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setCentralWidget(QWidget())

        self.__backend = Backend(connection)

        self.queryTabs = QueryTabViewer(self)
        self.database = QLabel("Current Database:")
        self.databaseTree = QTreeWidget()
        self.table = QLabel("Current Table:")
        self.tableStructure = TableStructureView()
        self.tableData = TableDataView()
        self.displayedTable: str = ''
        self.displayedDatabase: str = ''

        self.genDatabaseList()

        self.databaseTree.setHeaderHidden(True)
        self.databaseTree.itemSelectionChanged.connect(self.prepareTableInfo)
        self.databaseTree.itemChanged.connect(self.itemEdited)

        self.databaseTree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.databaseTree.customContextMenuRequested.connect(self.prepareMenu)

        self.tableDetails = QTabWidget()
        self.tableDetails.addTab(self.tableStructure, "Structure")
        self.tableDetails.addTab(self.tableData, "Data")

        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addAction("Open File", self.queryTabs.currentWidget().openFile,
                                QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_O))
        self.fileMenu.addAction("Save File", self.queryTabs.currentWidget().saveFile,
                                QKeyCombination(Qt.Modifier.CTRL, Qt.Key.Key_S))
        self.fileMenu.addAction("Save File As", self.queryTabs.currentWidget().saveFileAs,
                                QKeyCombination(Qt.Modifier.CTRL | Qt.Modifier.SHIFT, Qt.Key.Key_S))

        self.executeAction = self.menuBar().addAction(
            "Execute Query", QKeyCombination(Qt.Modifier.SHIFT, Qt.Key.Key_F10),
            lambda: self.executeQueries(self.queryTabs.currentWidget().queryBox.toPlainText().replace('\n', ' '))
        )

        self.refreshAction = self.menuBar().addAction("Refresh", Qt.Key.Key_F5, self.refresh)

        databaseWidget = QWidget()
        databaseLayout = QVBoxLayout()
        databaseLayout.addWidget(self.database)
        databaseLayout.addWidget(self.databaseTree)
        databaseWidget.setLayout(databaseLayout)

        tableWidget = QWidget()
        tableLayout = QVBoxLayout()
        tableLayout.addWidget(self.table)
        tableLayout.addWidget(self.tableDetails)
        tableWidget.setLayout(tableLayout)

        self.databaseSplitter = QSplitter()
        self.databaseSplitter.addWidget(databaseWidget)
        self.databaseSplitter.addWidget(tableWidget)
        self.databaseSplitter.setOrientation(Qt.Orientation.Vertical)

        splitter = QSplitter()
        splitter.addWidget(self.databaseSplitter)
        splitter.addWidget(self.queryTabs)
        splitter.splitterMoved.connect(lambda: self.changeModes(splitter.sizes()))

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.centralWidget().setLayout(layout)

    @Slot()
    def prepareMenu(self, pos: QPoint):
        item: QTreeWidgetItem = self.databaseTree.itemAt(pos)

        if item is None:
            menu = QMenu()

            menu.addAction("Add Database", lambda: AddDatabaseWindow(self.databaseTree).exec())

        elif not item.parent():
            database: str = item.text(0)

            if database in ("information_schema", "mysql", "sys", "performance"):
                return

            menu = QMenu()

            menu.addAction("Drop Database", lambda: self.dropDatabase(database))

        elif not item.parent().parent():
            return

        else:
            database: str = item.parent().parent().text(0)

            if database in ("information_schema", "mysql", "sys", "performance"):
                return

            menu = QMenu()

            menu.addAction("Drop Table", lambda: self.dropTable(item.text(0), database))

        menu.exec(pos)

    @Slot()
    def dropTable(self, table: str, database: str):
        if QMessageBox.question(
                self, "Confirmation",
                f"Are you sure you want to delete {table} from {database}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        error: Optional[Error] = self.__backend.dropTable(database, table)

        if error is not None:
            QMessageBox.critical(self, "Error", error.msg)

            return

        QMessageBox.information(self, "Success", "Successfully dropped!")

        self.tableStructure.clearData()
        self.tableData.clearData()

        for i in range(self.databaseTree.topLevelItemCount()):
            if self.databaseTree.topLevelItem(i).text(0) != database:
                continue

            for j in range(self.databaseTree.topLevelItem(i).childCount()):
                if self.databaseTree.topLevelItem(i).child(j).text(0) != table:
                    continue

                self.databaseTree.topLevelItem(i).takeChild(j)

                break

            else:
                continue

            break

        self.table.setText(f"Current Table: ")
        self.displayedTable = ""

    @Slot()
    def dropDatabase(self, database: str):
        if QMessageBox.question(
                self, "Confirmation",
                f"Are you sure you want to delete {database}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        error: Optional[Error] = self.__backend.dropDatabase(database)

        if error is not None:
            QMessageBox.critical(self, "Error", error.msg)

            return

        item = self.databaseTree.currentItem()

        if item.parent():
            item = item.parent()

            if item.parent():
                item = item.parent()

        self.databaseTree.blockSignals(True)

        self.databaseTree.takeTopLevelItem(self.databaseTree.indexOfTopLevelItem(item))

        self.databaseTree.setCurrentItem(None)

        self.databaseTree.blockSignals(False)

        self.tableStructure.clearData()
        self.tableData.clearData()

        self.database.setText("Current Database:")
        self.table.setText("Current Text:")

        QMessageBox.information(self, "Success", "Successfully Dropped!")

    def genDatabaseList(self):
        self.databaseTree.blockSignals(True)

        for (database,) in self.__backend.getDatabases():
            databaseItem = QTreeWidgetItem(self.databaseTree, (database,))

            tablesItem = QTreeWidgetItem(databaseItem, ("Tables",))
            viewsItem = QTreeWidgetItem(databaseItem, ("Views",))

            if database in ("mysql", "sys", "performance"):
                for table in self.__backend.getTables(database, "BASE TABLE"):
                    tablesItem.addChild(QTreeWidgetItem(table))

                for table in self.__backend.getTables(database, "VIEW"):
                    viewsItem.addChild(QTreeWidgetItem(table))

            if database == "information_schema":
                for table in self.__backend.getTables(database, "SYSTEM VIEW"):
                    viewsItem.addChild(QTreeWidgetItem(table))

            else:
                for table in self.__backend.getTables(database, "BASE TABLE"):
                    tableItem = QTreeWidgetItem(tablesItem, table)
                    tableItem.setFlags(tableItem.flags() | Qt.ItemFlag.ItemIsEditable)

                for table in self.__backend.getTables(database, "VIEW"):
                    tableItem = QTreeWidgetItem(viewsItem, table)
                    tableItem.setFlags(tableItem.flags() | Qt.ItemFlag.ItemIsEditable)

        self.databaseTree.blockSignals(False)

    @Slot(QTreeWidgetItem)
    def itemEdited(self, item: QTreeWidgetItem):
        if not item.parent().parent():
            return

        database: str = item.parent().parent().text(0)

        existing: List[str] = [table for (table, _) in
                               self.__backend.getTables(database, "BASE TABLE") + self.__backend.getTables(database,
                                                                                                           "VIEW")]

        for index in range(item.childCount()):
            text: str = item.child(index).text(0)

            if text not in existing:
                continue

            existing.remove(text)

        if not existing:
            return

        error: Optional[Error] = self.__backend.renameTable(database, existing[0], item.text(0))

        if error is not None:
            QMessageBox.critical(self, "Error", error.msg)

            return

        self.table.setText(f"Current Table: `{item.text(0)}` From `{database}`")
        self.displayedTable = item.text(0)

    @Slot()
    def changeModes(self, sizes):
        queryBoxSize = sizes[1]

        self.fileMenu.setEnabled(queryBoxSize)
        self.executeAction.setEnabled(queryBoxSize)
        self.refreshAction.setEnabled(sizes[0])

        if queryBoxSize:
            self.databaseSplitter.setOrientation(Qt.Orientation.Vertical)

        else:
            self.databaseSplitter.setOrientation(Qt.Orientation.Horizontal)

    @Slot()
    def prepareTableInfo(self):
        item = self.databaseTree.currentItem()

        if item is None:
            return

        if item.parent() is not None:
            if item.parent().parent() is not None:
                self.showTableInfo(item.parent().parent().text(0), item.text(0))

                self.displayedDatabase = item.parent().parent().text(0)

            else:
                self.displayedDatabase = item.parent().text(0)

        else:
            self.displayedDatabase = item.text(0)

        self.__backend.setDatabase(self.displayedDatabase)

        self.database.setText(f"Current Database: {self.displayedDatabase}")

    @Slot()
    def showTableInfo(self, database, table):
        self.displayedTable = table
        self.displayedDatabase = database

        self.table.setText(f"Current Table: `{table}` From `{database}`")

        self.tableStructure.setTable(database, table)
        self.tableData.setTable(database, table)

    @Slot()
    def executeQueries(self, queries: str):
        if not queries.strip():
            return

        queryList: List[str] = queries.split(';')

        tab: QueryTab = self.queryTabs.currentWidget()

        tab.results.clear()

        count = 1

        for i, query in enumerate(queryList):
            query: str = query.strip()

            if not query:
                continue

            result: Union[Error, Tuple[List[Any], List[str]]] = self.__backend.executeQuery(query)

            if isinstance(result, Error):
                QMessageBox.critical(self, f"Error executing query", f"In query {i + 1}:\n\n{query}\n\n{result.msg}")

                break

            queryUpper: str = query.upper()

            if "USE" in queryUpper:
                index = 4

                while query[index] == " ":
                    index += 1

                if query[index] == "`":
                    index += 1

                    self.database.setText(f"Current Database: {query[index:-1]}")

                else:
                    self.database.setText(f"Current Database: {query[index:]}")

            elif any(clause in queryUpper for clause in ("SELECT", "SHOW", "EXPLAIN", "DESC", "DESCRIBE")):
                data, columns = result

                table = QTableWidget(len(data), len(columns))
                table.setHorizontalHeaderLabels(columns)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

                for row, datum in enumerate(data):
                    for col, value in enumerate(datum):
                        if isinstance(value, bytes):
                            value = value.decode("utf-8")

                        table.setCellWidget(row, col, QLabel(f'{value}'))

                table.resizeColumnsToContents()

                tab.results.addTab(table, f"Result - {count}")

                count += 1

            elif any(clause in queryUpper for clause in ("ALTER", "CREATE", "DROP", "RENAME")):
                self.refresh()

        tab.results.setHidden(not tab.results.count())

    @Slot()
    def refresh(self):
        self.database.setText("Current Database:")
        self.databaseTree.clear()
        self.table.setText("Current Table:")
        self.tableStructure.clearData()
        self.tableData.clearData()
        self.genDatabaseList()
        self.queryTabs.currentWidget().results.hide()

        self.tableData.setActionsClickable(False)

    def closeEvent(self, event):
        if self.queryTabs.checkSave():
            event.accept()

        else:
            event.ignore()
