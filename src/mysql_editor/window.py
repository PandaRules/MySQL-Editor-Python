from typing import List, Union, Iterable

import mysql.connector.errors
from PySide6.QtCore import Slot, Qt, QDate, QKeyCombination, QDateTime, QPoint
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QComboBox, QDateEdit,
    QAbstractItemView, QDateTimeEdit, QMenu
)
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from mysql_editor.add_database import AddDatabaseWindow
from mysql_editor.query import QueryTab
from mysql_editor.table_data_view import TableDataView
from mysql_editor.table_structure_view import TableStructureView


class Window(QMainWindow):
    def __init__(self, connection: MySQLConnection):
        super().__init__(None)

        self.setWindowTitle("MySQL Editor")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setCentralWidget(QWidget())

        self.Cursor: MySQLCursor = connection.cursor()

        self.queryTabs = QTabWidget()
        self.database = QLabel("Current Database:")
        self.databaseTree = QTreeWidget()
        self.table = QLabel("Current Table:")
        self.tableStructure = TableStructureView()
        self.tableData = TableDataView()
        self.displayedTable: str = ''
        self.displayedDatabase: str = ''

        addButton = QPushButton("+")
        addButton.clicked.connect(self.addQueryTab)

        self.queryTabs.setCornerWidget(addButton)
        self.queryTabs.addTab(QueryTab(self.queryTabs), "Tab - 1")

        self.queryTabs.setTabsClosable(True)
        self.queryTabs.tabCloseRequested.connect(self.removeQueryTab)

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

        tableMenu = self.menuBar().addMenu("Table")
        tableMenu.addAction("Add New Entry", lambda: self.tableData.setRowCount(self.tableData.rowCount() + 1))
        tableMenu.addAction("Save Changes", lambda: self.saveEdits(self.displayedDatabase, self.displayedTable))
        tableMenu.addAction("Cancel Changes", lambda: self.showTableInfo(self.displayedDatabase, self.displayedTable))

        self.tableActions = tableMenu.actions()

        self.tableActions[0].setEnabled(False)
        self.tableActions[1].setEnabled(False)
        self.tableActions[2].setEnabled(False)

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

        menu = QMenu()

        if item is None:
            menu.addAction("Add Database", lambda: AddDatabaseWindow(self.Cursor, self.databaseTree).exec())

        elif not item.parent():
            database: str = item.text(0)

            if database in ("information_schema", "mysql", "sys", "performance"):
                return

            menu.addAction("Drop Database", lambda: self.dropDatabase(database))

        else:
            database: str = item.parent().text(0)

            if database in ("information_schema", "mysql", "sys", "performance"):
                return

            menu.addAction("Drop Table", lambda: self.dropTable(item.text(0), database))

        menu.exec(pos)

    @Slot()
    def addQueryTab(self):
        tabs = sorted(
            int(split[-1]) for split in
            (self.queryTabs.tabText(num).replace('&', '').split(" ") for num in range(self.queryTabs.count()))
            if "".join(split[:2]) == "Tab-" and split[-1].isdigit()
        )

        count = 1

        while count in tabs:
            count += 1

        self.queryTabs.addTab(QueryTab(self.queryTabs), f"Tab - {count}")

    @Slot(int)
    def removeQueryTab(self, index):
        if self.queryTabs.count() != 1:
            self.queryTabs.removeTab(index)

    @Slot()
    def dropTable(self, table: str, database: str):
        if QMessageBox.question(
                self, "Confirmation",
                f"Are you sure you want to delete {table} from {database}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        try:
            self.Cursor.execute(f"DROP TABLE `{database}`.`{table}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error", e.msg)

            return

        QMessageBox.information(self, "Success", "Successfully dropped!")

        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)
        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)

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

        try:
            self.Cursor.execute(f"DROP DATABASE `{database}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error", e.msg)

            return

        item = self.databaseTree.currentItem()

        if item.parent():
            item = item.parent()

        self.databaseTree.blockSignals(True)

        self.databaseTree.takeTopLevelItem(self.databaseTree.indexOfTopLevelItem(item))

        self.databaseTree.setCurrentItem(None)

        self.databaseTree.blockSignals(False)

        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)
        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)

        self.database.setText("Current Database:")
        self.table.setText("Current Text:")

        QMessageBox.information(self, "Success", "Successfully Dropped!")

    def genDatabaseList(self):
        self.Cursor.execute("SHOW DATABASES;")

        for database in self.Cursor.fetchall():
            databaseItem = QTreeWidgetItem(database)
            self.databaseTree.addTopLevelItem(databaseItem)

            self.Cursor.execute(f"SHOW TABLES FROM `{database[0]}`")

            if database[0] in ("information_schema", "mysql", "sys", "performance"):
                for table in self.Cursor.fetchall():
                    databaseItem.addChild(QTreeWidgetItem(table))

            else:
                for table in self.Cursor.fetchall():
                    tableItem = QTreeWidgetItem(table)
                    tableItem.setFlags(tableItem.flags() | Qt.ItemFlag.ItemIsEditable)

                    databaseItem.addChild(tableItem)

    @Slot(QTreeWidgetItem)
    def itemEdited(self, item: QTreeWidgetItem):
        if not item.parent():
            return

        database: str = item.parent().text(0)

        self.Cursor.execute(f"SHOW TABLES FROM {database};")
        existing: list[str] = [tuple_[0] for tuple_ in self.Cursor.fetchall()]

        for index in range(item.childCount()):
            text: str = item.child(index).text(0)

            if text not in existing:
                continue

            existing.remove(text)

        if not existing:
            return

        try:
            self.Cursor.execute(f"RENAME TABLE `{database}`.`{existing[0]}` TO `{database}`.`{item.text(0)}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error renaming table", e.msg)

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

        if item.parent():
            self.showTableInfo(item.parent().text(0), item.text(0))

            item = item.parent()

        self.displayedDatabase = item.text(0)

        self.Cursor.execute(f"USE `{self.displayedDatabase}`")

        self.database.setText(f"Current Database: {self.displayedDatabase}")

    @Slot()
    def showTableInfo(self, database, table):
        self.displayedTable = table
        self.displayedDatabase = database

        self.table.setText(f"Current Table: `{table}` From `{database}`")

        self.Cursor.execute(f"DESC `{database}`.`{table}`;")
        structure = self.Cursor.fetchall()

        self.tableStructure.clear()
        self.tableStructure.setColumnCount(len(structure))
        self.tableStructure.setRowCount(len(self.Cursor.column_names) - 1)
        self.tableStructure.setVerticalHeaderLabels(self.Cursor.column_names[1:])

        for row, tuple_ in enumerate(structure):
            for col, value in enumerate(tuple_[1:]):
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                self.tableStructure.setCellWidget(col, row, QLabel(value))

        self.Cursor.execute(f'SELECT * FROM `{database}`.`{table}`;')

        data = self.Cursor.fetchall()

        self.tableData.clear()
        self.tableData.setRowCount(len(data))
        self.tableData.setColumnCount(len(self.Cursor.column_names))
        self.tableData.setHorizontalHeaderLabels(self.Cursor.column_names)
        self.tableStructure.setHorizontalHeaderLabels(self.Cursor.column_names)

        for row, tuple_ in enumerate(data):
            self.tableData.setRowHidden(row, False)

            for col, value in enumerate(tuple_):
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                if structure[col][1][:4] == "enum":
                    options = QComboBox()
                    options.addItems(eval(structure[col][1][4:]))
                    options.setCurrentText(f"{value}")

                    self.tableData.setCellWidget(row, col, options)

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

                    self.tableData.setCellWidget(row, col, date)

                elif structure[col][1] == "datetime":
                    currentDate = QDateTime.fromString(f"{value}", "yyyy-MM-dd hh:mm:ss")

                    date = QDateTimeEdit()
                    date.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
                    date.setCalendarPopup(True)

                    if currentDate < date.minimumDate():
                        date.setMinimumDate(currentDate)

                    elif currentDate > date.maximumDate():
                        date.setMaximumDate(currentDate)

                    if structure[col][2] != "":
                        default = QDateTime.fromString(f"{structure[col][2]}", "yyyy-MM-dd hh:mm:ss")

                        if default < date.minimumDate():
                            date.setMinimumDate(default)

                        elif default > date.maximumDate():
                            date.setMaximumDate(default)

                    date.setDate(currentDate)

                    self.tableData.setCellWidget(row, col, date)

                else:
                    self.tableData.setItem(row, col, QTableWidgetItem(f"{value}"))

        self.tableActions[0].setEnabled(True)
        self.tableActions[1].setEnabled(True)
        self.tableActions[2].setEnabled(True)

        if database in ("information_schema", "mysql", "sys", "performance"):
            self.tableData.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.tableData.verticalHeader().setToolTip("")
            self.tableData.verticalHeader().sectionClicked.disconnect(self.tableData.updateDeleted)

        else:
            self.tableData.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked |
                QAbstractItemView.EditTrigger.EditKeyPressed |
                QAbstractItemView.EditTrigger.AnyKeyPressed
            )
            self.tableData.verticalHeader().setToolTip("Click to remove row")
            self.tableData.verticalHeader().sectionClicked.connect(self.tableData.updateDeleted)

    @Slot()
    def saveEdits(self, database: str, table: str):
        unique, uniqueCol = self.tableData.getUnique()

        rowCount = 0

        queries: List[str] = []
        parameters: List[Iterable] = []

        self.Cursor.execute(f'SELECT * FROM `{database}`.`{table}`')

        for row, tuple_ in enumerate(self.Cursor.fetchall()):
            uniqueValue = self.tableData.item(row, uniqueCol).text()

            if row in self.tableData.deleted:
                queries.append(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s")
                parameters.append((uniqueValue,))

                continue

            changedValues: List[str] = []

            query = ""

            for col in range(self.tableData.columnCount()):
                cell = self.tableData.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.tableData.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateTimeEdit):
                        value = cell.dateTime().toString("yyyy-MM-dd hh:mm:ss")

                    else:
                        value = cell.date().toString("yyyy-MM-dd")

                if value == f"{tuple_[col]}":
                    continue

                changedValues.append(value)
                query += f"`{self.tableStructure.horizontalHeaderItem(col).text()}` = %s, "

            if query:
                queries.append(f"UPDATE `{database}`.`{table}` SET {query[:-2]} WHERE `{unique}` = '{uniqueValue}'")
                parameters.append(changedValues)

            rowCount += 1

        for row in range(rowCount, self.tableData.rowCount()):
            query: str = ""
            changedValues: List[str] = []

            for col in range(self.tableData.columnCount()):
                cell: QTableWidgetItem = self.tableData.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell: Union[QComboBox, QDateEdit, QDateTimeEdit] = self.tableData.cellWidget(row, col)

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

        try:
            for query, parameter in zip(queries, parameters):
                self.Cursor.execute(query, parameter)

        except mysql.connector.errors.Error as error:
            QMessageBox.critical(self, "Error", error.msg)

            return

        QMessageBox.information(self, "Success", "Successfully Executed")

        self.tableData.resizeColumnsToContents()

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

            try:
                self.Cursor.execute(query)

            except mysql.connector.errors.Error as error:
                QMessageBox.critical(self, f"Error executing query", f"In query {i + 1}:\n\n{query}\n\n{error.msg}")

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
                data = self.Cursor.fetchall()
                table = QTableWidget(len(data), len(self.Cursor.column_names))
                table.setHorizontalHeaderLabels(self.Cursor.column_names)
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
        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)
        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)
        self.genDatabaseList()
        self.queryTabs.currentWidget().results.hide()

        self.tableActions[0].setEnabled(False)
        self.tableActions[1].setEnabled(False)
        self.tableActions[2].setEnabled(False)

    def closeEvent(self, event):
        for index in range(self.queryTabs.count()):
            if self.queryTabs.tabText(index)[:2] != "* ":
                continue

            option = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"You have unsaved changes in {self.queryTabs.tabText(index)[2:]}. Would you like to save them?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if option == QMessageBox.StandardButton.Cancel:
                event.ignore()

                return

            if option == QMessageBox.StandardButton.Save:
                self.queryTabs.widget(index).save()

        event.accept()
