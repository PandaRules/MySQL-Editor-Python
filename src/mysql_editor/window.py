from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import Error

from mysql_editor.add_database import AddDatabaseWindow
from mysql_editor.drop_database import DropDatabaseWindow
from mysql_editor.drop_table import DropTableWindow
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

        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_query_tab)

        self.queryTabs.setCornerWidget(add_button)
        self.queryTabs.addTab(QueryTab(self.queryTabs), "Query - 1")
        self.queryTabs.setTabsClosable(True)
        self.queryTabs.tabCloseRequested.connect(self.remove_query_tab)

        self.databases.setHeaderHidden(True)
        self.databases.currentItemChanged.connect(self.prepare_table_info)

        self.tableData.verticalHeader().setToolTip("Click to remove row")
        self.tableData.verticalHeader().sectionClicked.connect(
            lambda: self.tableData.hideRow(self.tableData.currentRow())
        )

        self.tableStructure.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tableData.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

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

        database_menu = self.menuBar().addMenu("Database")
        database_menu.addAction("Add database", lambda: AddDatabaseWindow(self.Cursor, self.databases).exec())
        database_menu.addAction("Drop database", lambda: DropDatabaseWindow(self.Cursor, self.databases).exec())

        table_menu = self.menuBar().addMenu("Table")
        table_menu.addAction("Drop Table", lambda: DropTableWindow(self.Cursor, self.databases).exec())
        table_menu.addSeparator()
        table_menu.addAction("Add New Entry", lambda: self.tableData.setRowCount(self.tableData.rowCount() + 1))
        table_menu.addAction("Save Changes", lambda: self.save_edits(self.displayedDatabase, self.displayedTable))
        table_menu.addAction("Cancel Changes",
                             lambda: self.show_table_info(self.displayedDatabase, self.displayedTable))

        self.tableActions = table_menu.actions()

        self.tableActions[2].setEnabled(False)
        self.tableActions[3].setEnabled(False)
        self.tableActions[4].setEnabled(False)

        database_layout = QVBoxLayout()
        database_layout.addWidget(self.database)
        database_layout.addWidget(self.databases)
        database_layout.addWidget(self.table)
        database_layout.addWidget(self.tableStructure)
        database_layout.addWidget(self.tableData)

        database_layout_widget = QWidget()
        database_layout_widget.setLayout(database_layout)

        splitter = QSplitter()
        splitter.addWidget(self.queryTabs)
        splitter.addWidget(database_layout_widget)
        splitter.splitterMoved.connect(lambda: self.change_modes(splitter.sizes()))

        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().addWidget(splitter)

        self.gen_database_list()

    @Slot()
    def add_query_tab(self):
        count = 1

        for i in range(self.queryTabs.count()):
            if self.queryTabs.widget(i).file is None:
                count += 1

        self.queryTabs.addTab(QueryTab(self.queryTabs), f"Query - {count}")

    @Slot(int)
    def remove_query_tab(self, index):
        if self.queryTabs.count() != 1:
            self.queryTabs.removeTab(index)

    def gen_database_list(self):
        self.Cursor.execute("SHOW DATABASES;")

        for row in self.Cursor.fetchall():
            database = QTreeWidgetItem(row)
            self.databases.addTopLevelItem(database)

            self.Cursor.execute(f"SHOW TABLES FROM `{row[0]}`")

            for table in self.Cursor.fetchall():
                database.addChild(QTreeWidgetItem(table))

    @Slot()
    def change_modes(self, sizes):
        query_box_size = sizes[0]

        self.fileMenu.setEnabled(query_box_size)
        self.executeAction.setEnabled(query_box_size)
        self.refreshAction.setEnabled(sizes[1])

        self.database.setHidden(not query_box_size)

    @Slot(QTreeWidgetItem)
    def prepare_table_info(self, item):
        if item.parent():
            self.show_table_info(item.parent().text(0), item.text(0))

            return

        self.displayedDatabase = item.text(0)

        self.Cursor.execute(f"USE `{self.displayedDatabase}`")

        self.database.setText(f"Current Database: {self.displayedDatabase}")

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

        self.tableData.setRowCount(len(data))
        self.tableData.setColumnCount(len(self.Cursor.column_names))
        self.tableData.setHorizontalHeaderLabels(self.Cursor.column_names)
        self.tableStructure.setHorizontalHeaderLabels(self.Cursor.column_names)

        for row, tuple_ in enumerate(data):
            self.tableData.setRowHidden(row, False)

            for col, value in enumerate(tuple_):
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                self.tableData.setItem(row, col, QTableWidgetItem(f"{value}"))

        self.tableActions[2].setEnabled(True)
        self.tableActions[3].setEnabled(True)
        self.tableActions[4].setEnabled(True)

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

        self.Cursor.execute(f'SELECT * FROM `{database}`.`{table}`')

        database_values = {row: values for row, values in enumerate(self.Cursor.fetchall())}

        try:
            for row in range(self.tableData.rowCount()):
                unique_value = self.tableData.item(row, unique_col).text()

                if self.tableData.isRowHidden(row):
                    self.Cursor.execute(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s", (unique_value,))

                    continue

                changed_values = []

                query = ""

                database_row = database_values.get(row)

                if database_row is None:
                    for col in range(self.tableData.columnCount()):
                        changed_values.append(self.tableData.item(row, col).text())
                        query += "%s, "

                    final_query = f"INSERT INTO `{database}`.`{table}` VALUES ({query[:-2]});"

                else:
                    for col in range(self.tableData.columnCount()):
                        value = self.tableData.item(row, col).text()

                        if value == f"{database_row[col]}":
                            continue

                        changed_values.append(value)
                        query += f"`{self.tableStructure.horizontalHeaderItem(col).text()}` = %s, "

                    final_query = f"UPDATE `{database}`.`{table}` SET {query[:-2]} WHERE `{unique}` = '{unique_value}'"

                if query:
                    self.Cursor.execute(final_query, changed_values)

        except Error as error:
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

                        final = -2

                    else:
                        final = -1

                    self.database.setText(f"Current Database: {query[index:final]}")

                elif any(clause in query_upper for clause in ("SELECT", "SHOW", "EXPLAIN", "DESCRIBE", "DESC")):
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

        except Error as error:
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

        self.tableActions[2].setEnabled(False)
        self.tableActions[3].setEnabled(False)
        self.tableActions[4].setEnabled(False)

    def closeEvent(self, event):
        edited_files: list[QueryTab] = []

        for index in range(self.queryTabs.count()):
            if self.queryTabs.tabText(index)[:2] != "* ":
                continue

            edited_files.append(self.queryTabs.widget(index))

        if not edited_files:
            event.accept()

            return

        option = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Would you like to save them?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )

        if option == QMessageBox.StandardButton.Cancel:
            event.ignore()

            return

        if option == QMessageBox.StandardButton.Save:
            for file in edited_files:
                file.save_file()

        event.accept()
