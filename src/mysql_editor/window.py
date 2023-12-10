import mysql.connector.errors
from PySide6.QtCore import Slot, Qt, QDate
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QComboBox, QDateEdit,
    QAbstractItemView, QHBoxLayout
)
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from mysql_editor.add_database import AddDatabaseWindow
from mysql_editor.query import QueryTab


class Window(QMainWindow):
    def __init__(self, connection: MySQLConnection):
        super().__init__(None)

        self.setWindowTitle("MySQL Editor")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setCentralWidget(QWidget())

        self.Cursor: MySQLCursor = connection.cursor()

        self.queryTabs = QTabWidget()
        self.database = QLabel("Current Database:")
        self.databases = QTreeWidget()
        self.table = QLabel("Current Table:")
        self.tableStructure = QTableWidget()
        self.tableData = QTableWidget()
        self.displayedTable: str = ''
        self.displayedDatabase: str = ''
        self.deleted: list[int] = []

        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_query_tab)

        self.queryTabs.setCornerWidget(add_button)
        self.queryTabs.addTab(QueryTab(self.queryTabs), "Tab - 1")

        self.queryTabs.setTabsClosable(True)
        self.queryTabs.tabCloseRequested.connect(self.remove_query_tab)

        self.gen_database_list()

        self.databases.setHeaderHidden(True)
        self.databases.itemSelectionChanged.connect(self.prepare_table_info)

        self.tableData.verticalHeader().setToolTip("Click to remove row")
        self.tableData.verticalHeader().sectionClicked.connect(self.update_deleted)

        self.tableStructure.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tableData.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.dropTableButton = QPushButton("Drop Table")
        self.dropTableButton.setEnabled(False)
        self.dropTableButton.clicked.connect(self.drop_table)

        self.dropDatabaseButton = QPushButton("Drop Database")
        self.dropDatabaseButton.clicked.connect(self.drop_database)
        self.dropDatabaseButton.setEnabled(False)

        self.tableDetails = QTabWidget()
        self.tableDetails.addTab(self.tableStructure, "Structure")
        self.tableDetails.addTab(self.tableData, "Data")
        self.tableDetails.setCornerWidget(self.dropTableButton)

        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addAction("Open File", self.queryTabs.currentWidget().open_file, Qt.Modifier.CTRL | Qt.Key.Key_O)
        self.fileMenu.addAction("Save File", self.queryTabs.currentWidget().save_file, Qt.Modifier.CTRL | Qt.Key.Key_S)
        self.fileMenu.addAction("Save File As", self.queryTabs.currentWidget().save_file_as,
                                Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_S)

        self.executeAction = self.menuBar().addAction(
            "Execute Query", Qt.Modifier.SHIFT | Qt.Key.Key_F10,
            lambda: self.execute_query(self.queryTabs.currentWidget().queryBox.toPlainText().replace('\n', ' '))
        )

        self.refreshAction = self.menuBar().addAction("Refresh", Qt.Key.Key_F5, self.refresh)

        table_menu = self.menuBar().addMenu("Table")
        table_menu.addAction("Add New Entry", lambda: self.tableData.setRowCount(self.tableData.rowCount() + 1))
        table_menu.addAction("Save Changes", lambda: self.save_edits(self.displayedDatabase, self.displayedTable))
        table_menu.addAction("Cancel Changes",
                             lambda: self.show_table_info(self.displayedDatabase, self.displayedTable))

        self.tableActions = table_menu.actions()

        self.tableActions[0].setEnabled(False)
        self.tableActions[1].setEnabled(False)
        self.tableActions[2].setEnabled(False)

        database_details = QHBoxLayout()
        database_details.addWidget(self.database)
        database_details.addWidget(self.dropDatabaseButton)

        database_widget = QWidget()
        database_layout = QVBoxLayout()
        database_layout.addLayout(database_details)
        database_layout.addWidget(self.databases)
        database_widget.setLayout(database_layout)

        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_layout.addWidget(self.tableDetails)
        table_widget.setLayout(table_layout)

        self.databaseSplitter = QSplitter()
        self.databaseSplitter.addWidget(database_widget)
        self.databaseSplitter.addWidget(table_widget)
        self.databaseSplitter.setOrientation(Qt.Orientation.Vertical)

        splitter = QSplitter()
        splitter.addWidget(self.databaseSplitter)
        splitter.addWidget(self.queryTabs)
        splitter.splitterMoved.connect(lambda: self.change_modes(splitter.sizes()))

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.centralWidget().setLayout(layout)

    @Slot(int)
    def update_deleted(self, row):
        deleted = row in self.deleted

        if row in self.deleted:
            self.deleted.remove(row)

        else:
            self.deleted.append(row)

        for col in range(self.tableData.columnCount()):
            try:
                self.tableData.cellWidget(row, col).setEnabled(deleted)

            except AttributeError:
                self.tableData.item(row, col).setEnabled(deleted)

    @Slot()
    def add_query_tab(self):
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
    def remove_query_tab(self, index):
        if self.queryTabs.count() != 1:
            self.queryTabs.removeTab(index)

    @Slot()
    def drop_table(self):
        if QMessageBox.question(
                self, "Confirmation",
                f"Are you sure you want to delete {self.displayedTable} from {self.displayedDatabase}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        try:
            self.Cursor.execute(f"DROP TABLE `{self.displayedDatabase}`.`{self.displayedTable}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error", e.msg)

            return

        QMessageBox.information(self, "Success", "Successfully dropped!")

        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)
        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)

        for i in range(self.databases.topLevelItemCount()):
            if self.databases.topLevelItem(i).text(0) != self.displayedDatabase:
                continue

            for j in range(self.databases.topLevelItem(i).childCount()):
                if self.databases.topLevelItem(i).child(j).text(0) != self.displayedTable:
                    continue

                self.databases.topLevelItem(i).takeChild(j)

                break

            else:
                continue

            break

    @Slot()
    def drop_database(self):
        if QMessageBox.question(
                self, "Confirmation",
                f"Are you sure you want to delete {self.displayedDatabase}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        try:
            self.Cursor.execute(f"DROP DATABASE `{self.displayedDatabase}`;")

        except mysql.connector.errors.Error as e:
            QMessageBox.critical(self, "Error", e.msg)

            return

        item = self.databases.currentItem()

        if item.parent():
            item = item.parent()

        self.databases.blockSignals(True)

        self.databases.takeTopLevelItem(self.databases.indexOfTopLevelItem(item))

        self.databases.setCurrentItem(None)

        self.databases.blockSignals(False)

        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)
        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)

        QMessageBox.information(self, "Success", "Successfully Dropped!")

    def gen_database_list(self):
        self.Cursor.execute("SHOW DATABASES;")

        for row in self.Cursor.fetchall():
            database = QTreeWidgetItem(row)
            self.databases.addTopLevelItem(database)

            self.Cursor.execute(f"SHOW TABLES FROM `{row[0]}`")

            for table in self.Cursor.fetchall():
                database.addChild(QTreeWidgetItem(table))

        self.databases.addTopLevelItem(QTreeWidgetItem(("Add new Database",)))

    @Slot()
    def change_modes(self, sizes):
        query_box_size = sizes[1]

        self.fileMenu.setEnabled(query_box_size)
        self.executeAction.setEnabled(query_box_size)
        self.refreshAction.setEnabled(sizes[0])

        if not query_box_size:
            self.databaseSplitter.setOrientation(Qt.Orientation.Horizontal)

        else:
            self.databaseSplitter.setOrientation(Qt.Orientation.Vertical)

    @Slot()
    def prepare_table_info(self):
        item = self.databases.currentItem()

        if item is None:
            self.dropDatabaseButton.setEnabled(False)

            return

        if item.parent():
            self.show_table_info(item.parent().text(0), item.text(0))

            item = item.parent()

        if self.databases.indexOfTopLevelItem(item) == self.databases.topLevelItemCount() - 1:
            self.dropDatabaseButton.setEnabled(False)

            AddDatabaseWindow(self.Cursor, self.databases).exec()

            self.databases.setCurrentItem(None)

            return

        self.displayedDatabase = item.text(0)

        self.Cursor.execute(f"USE `{self.displayedDatabase}`")

        self.database.setText(f"Current Database: {self.displayedDatabase}")

        self.dropDatabaseButton.setEnabled(True)

    @Slot()
    def show_table_info(self, database, table):
        self.displayedTable = table
        self.displayedDatabase = database

        self.table.setText(f"Current Table: `{table}` From `{database}`")

        self.Cursor.execute(f"DESC `{database}`.`{table}`;")
        structure = self.Cursor.fetchall()

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
                    current_date = QDate.fromString(f"{value}", "yyyy-MM-dd")

                    date = QDateEdit()
                    date.setDisplayFormat("yyyy-MM-dd")

                    if current_date < date.minimumDate():
                        date.setMinimumDate(current_date)

                    elif current_date > date.maximumDate():
                        date.setMaximumDate(current_date)

                    if structure[col][2] != "":
                        default = QDate.fromString(f"{structure[col][2]}", "yyyy-MM-dd")

                        if default < date.minimumDate():
                            date.setMinimumDate(default)

                        elif default > date.maximumDate():
                            date.setMaximumDate(default)

                    date.setDate(current_date)

                    self.tableData.setCellWidget(row, col, date)

                else:
                    self.tableData.setItem(row, col, QTableWidgetItem(f"{value}"))

        self.tableActions[0].setEnabled(True)
        self.tableActions[1].setEnabled(True)
        self.tableActions[2].setEnabled(True)

        if database in ("information_schema", "mysql", "sys", "performance"):
            self.tableData.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.tableData.verticalHeader().setToolTip("")
            self.tableData.verticalHeader().sectionClicked.disconnect(self.update_deleted)
            self.dropTableButton.setEnabled(False)

        else:
            self.tableData.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked |
                QAbstractItemView.EditTrigger.EditKeyPressed |
                QAbstractItemView.EditTrigger.AnyKeyPressed
            )
            self.tableData.verticalHeader().setToolTip("Click to remove row")
            self.tableData.verticalHeader().sectionClicked.connect(self.update_deleted)
            self.dropTableButton.setEnabled(True)

    @Slot()
    def save_edits(self, database, table):
        for col in range(self.tableStructure.columnCount()):
            if self.tableStructure.cellWidget(2, col).text() not in ("PRI", "UNI"):
                continue

            unique = self.tableStructure.horizontalHeaderItem(col).text()
            unique_col = col

            break

        else:
            unique = self.tableStructure.horizontalHeaderItem(0).text()
            unique_col = 0

        row_count = 0

        queries = []
        parameters = []

        self.Cursor.execute(f'SELECT * FROM `{database}`.`{table}`')

        for row, tuple_ in enumerate(self.Cursor.fetchall()):
            unique_value = self.tableData.item(row, unique_col).text()

            if row in self.deleted:
                queries.append(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s")
                parameters.append((unique_value,))

                continue

            changed_values = []

            query = ""

            for col in range(self.tableData.columnCount()):
                cell = self.tableData.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell = self.tableData.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateEdit):
                        value = cell.date().toString("yyyy-MM-dd")

                    else:
                        value = cell.text()

                if value == f"{tuple_[col]}":
                    continue

                changed_values.append(value)
                query += f"`{self.tableStructure.horizontalHeaderItem(col).text()}` = %s, "

            if query:
                queries.append(
                    f"UPDATE `{database}`.`{table}` SET {query[:-2]} WHERE `{unique}` = '{unique_value}'"
                )
                parameters.append(changed_values)

            row_count += 1

        for row in range(row_count, self.tableData.rowCount()):
            query = ""
            changed_values = []

            for col in range(self.tableData.columnCount()):
                cell = self.tableData.item(row, col)

                if cell is not None:
                    value = cell.text()

                else:
                    cell = self.tableData.cellWidget(row, col)

                    if isinstance(cell, QComboBox):
                        value = cell.currentText()

                    elif isinstance(cell, QDateEdit):
                        value = cell.date().toString("yyyy-MM-dd")

                    else:
                        value = cell.text()

                changed_values.append(value)
                query += "%s, "

            queries.append(f"INSERT INTO `{database}`.`{table}` VALUES ({query[:-2]});")
            parameters.append(changed_values)

        try:
            for query, parameter in zip(queries, parameters):
                self.Cursor.execute(query, parameter)

        except mysql.connector.errors.Error as error:
            QMessageBox.critical(self, "Error", error.msg)

            return

        QMessageBox.information(self, "Success", "Successfully Executed")

        self.tableData.resizeColumnsToContents()

    @Slot()
    def execute_query(self, queries):
        if not queries.strip():
            return

        query_list: list[str] = queries.split(';')

        tab: QueryTab = self.queryTabs.currentWidget()

        tab.results.clear()

        try:
            count = 1

            query: str
            for i, query in enumerate(query_list):
                query = query.strip()

                if not query:
                    continue

                self.Cursor.execute(query)

                query_upper = query.upper()

                if "USE" in query_upper:
                    index = 4

                    while query[index] == " ":
                        index += 1

                    if query[index] == "`":
                        index += 1

                        self.database.setText(f"Current Database: {query[index:-1]}")

                    else:
                        self.database.setText(f"Current Database: {query[index:]}")

                    self.dropDatabaseButton.setEnabled(True)

                elif any(clause in query_upper for clause in ("SELECT", "SHOW", "EXPLAIN", "DESC", "DESCRIBE")):
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

                elif any(clause in query_upper for clause in ("ALTER", "CREATE", "DROP", "RENAME")):
                    self.refresh()

        except mysql.connector.errors.Error as error:
            QMessageBox.critical(self, "Error", error.msg)

        else:
            QMessageBox.information(self, "Success", "Successfully executed!")

        tab.results.setHidden(not tab.results.count())

    @Slot()
    def refresh(self):
        self.database.setText("Current Database:")
        self.databases.clear()
        self.table.setText("Current Table:")
        self.tableStructure.setRowCount(0)
        self.tableStructure.setColumnCount(0)
        self.tableData.setRowCount(0)
        self.tableData.setColumnCount(0)
        self.gen_database_list()
        self.queryTabs.currentWidget().results.hide()
        self.dropDatabaseButton.setEnabled(False)
        self.dropTableButton.setEnabled(False)

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
