from os import getcwd, getenv, mkdir
from os.path import isdir, join, isfile
from pickle import load, dump
from sys import platform, exit

from PySide6.QtCore import Slot, Qt, QEventLoop
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLayout,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QSplitter, QStyleFactory, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)
from mysql.connector import connect
from mysql.connector.errors import Error
from requests import get
from requests.exceptions import ConnectionError

global connection

EXECUTABLE_NAME = "MySQL Editor.bin"
CONFIGURATOR_NAME = "MySQL Editor Configurator.bin"
EXECUTABLE_PATH = join(getenv("HOME"), ".local", "share", "MySQL Editor")
EXECUTABLE_FILE = join(EXECUTABLE_PATH, EXECUTABLE_NAME)
CONFIGURATOR_FILE = join(EXECUTABLE_PATH, CONFIGURATOR_NAME)
CONFIG_PATH = join(getenv("HOME"), ".config", "MySQL Editor")
UPDATE_FILE = join(CONFIG_PATH, "update.dat")


class Window(QMainWindow):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("MySQL Editor")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setCentralWidget(QWidget())

        self.Cursor = connection.cursor()

        self.queryTabs = QTabWidget()
        self.database = QLabel("Current Database:")
        self.databases = QTreeWidget()
        self.table = QLabel("Current Table:")
        self.tableStructure = QTableWidget()
        self.tableData = QTableWidget()
        self.tableMessage = QLabel("")
        self.displayedTable = ''
        self.displayedDatabase = ''

        self.openFileDialog = QFileDialog(caption="Open File")
        self.openFileDialog.setDefaultSuffix(".sql")
        self.openFileDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.openFileDialog.setNameFilter("SQL Query File (*.sql)")

        self.saveFileDialog = QFileDialog(caption="Save File")
        self.saveFileDialog.setDefaultSuffix(".sql")
        self.saveFileDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self.saveFileDialog.setNameFilter("SQL Query File (*.sql)")

        self.saveFileAsDialog = QFileDialog(caption="Save File As")
        self.saveFileAsDialog.setDefaultSuffix(".sql")
        self.saveFileAsDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self.saveFileAsDialog.setNameFilter("SQL Query File (*.sql)")

        self.currentWidget: QueryMode | None = None

        self.queryTabs.currentChanged.connect(lambda: self.updateQueryDetails(self.queryTabs.currentWidget()))
        self.queryTabs.addTab(QueryMode(self), "Query - 1")
        self.queryTabs.setTabsClosable(True)
        self.queryTabs.tabCloseRequested.connect(self.removeQueryTab)

        addButton = QPushButton("+")
        addButton.clicked.connect(self.addQueryTab)

        self.queryTabs.setCornerWidget(addButton)

        self.databases.setHeaderHidden(True)
        self.databases.currentItemChanged.connect(self.prepareTableInfo)

        self.tableData.verticalHeader().setToolTip("Click to remove row")
        self.tableData.verticalHeader().sectionClicked.connect(
            lambda: self.tableData.hideRow(self.tableData.currentItem().row())
        )

        self.tableStructure.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tableData.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.fileMenu = self.menuBar().addMenu("File")
        self.fileMenu.addAction("Open File", self.openFile, Qt.Modifier.CTRL | Qt.Key.Key_O)
        self.fileMenu.addAction("Save File", self.saveFile, Qt.Modifier.CTRL | Qt.Key.Key_S)
        self.fileMenu.addAction("Save File As", self.saveFileAs, Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_S)

        self.executeAction = self.menuBar().addAction(
            "Execute Query", Qt.Modifier.SHIFT | Qt.Key.Key_F10,
            lambda: self.executeQuery(self.currentWidget.queryBox.toPlainText().replace('\n', ' '))
        )

        self.refreshAction = self.menuBar().addAction("Refresh", Qt.Key.Key_F5, self.refresh)

        databaseMenu = self.menuBar().addMenu("Database")
        databaseMenu.addAction("Add database", lambda: AddDatabaseWindow(self).show())
        databaseMenu.addAction("Drop database", lambda: DropDatabaseWindow(self).show())

        tableMenu = self.menuBar().addMenu("Table")
        tableMenu.addAction("Drop Table", lambda: DropTableWindow(self).show())
        tableMenu.addSeparator()
        tableMenu.addAction("Add New Entry", lambda: self.tableData.setRowCount(self.tableData.rowCount() + 1))
        tableMenu.addAction("Save Changes", lambda: self.saveEdits(self.displayedDatabase, self.displayedTable))
        tableMenu.addAction("Cancel Changes", lambda: self.showTableInfo(self.displayedDatabase, self.displayedTable))

        self.tableActions = tableMenu.actions()

        self.tableActions[2].setEnabled(False)
        self.tableActions[3].setEnabled(False)
        self.tableActions[4].setEnabled(False)

        databaseLayout = QVBoxLayout()
        databaseLayout.addWidget(self.database)
        databaseLayout.addWidget(self.databases)
        databaseLayout.addWidget(self.table)
        databaseLayout.addWidget(self.tableStructure)
        databaseLayout.addWidget(self.tableData)
        databaseLayout.addWidget(self.tableMessage)

        databaseLayoutWidget = QWidget()
        databaseLayoutWidget.setLayout(databaseLayout)

        splitter = QSplitter()
        splitter.addWidget(self.queryTabs)
        splitter.addWidget(databaseLayoutWidget)
        splitter.splitterMoved.connect(lambda: self.changeModes(splitter.sizes()))

        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().addWidget(splitter)

        self.tableMessage.hide()

        self.genDatabaseList()

    @Slot()
    def addQueryTab(self):
        count = 1

        for i in range(self.queryTabs.count()):
            if self.queryTabs.widget(i).file is None:
                count += 1

        self.queryTabs.addTab(QueryMode(self), f"Query - {count}")

    @Slot(int)
    def removeQueryTab(self, index):
        if self.queryTabs.count() == 1:
            return

        self.queryTabs.removeTab(index)

    @Slot()
    def updateQueryDetails(self, widget):
        self.currentWidget = widget

    def genDatabaseList(self):
        self.Cursor.execute("SHOW DATABASES;")

        for row in self.Cursor.fetchall():
            database = QTreeWidgetItem(row)
            self.databases.addTopLevelItem(database)

            self.Cursor.execute(f"SHOW TABLES FROM `{row[0]}`")

            for table in self.Cursor.fetchall():
                database.addChild(QTreeWidgetItem(table))

    @Slot()
    def changeModes(self, sizes):
        queryBoxSize = sizes[0]

        self.fileMenu.setEnabled(queryBoxSize)
        self.executeAction.setEnabled(queryBoxSize)
        self.refreshAction.setEnabled(sizes[1])

        self.database.setHidden(not queryBoxSize)

    @Slot(QTreeWidgetItem)
    def prepareTableInfo(self, item):
        if item.parent():
            self.showTableInfo(item.parent().text(0), item.text(0))

            return

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

                self.tableData.setItem(row, col, QTableWidgetItem(f'{value}'))

        self.tableData.resizeColumnsToContents()

        self.tableActions[2].setEnabled(True)
        self.tableActions[3].setEnabled(True)
        self.tableActions[4].setEnabled(True)

    @Slot()
    def saveEdits(self, database, table):
        for col in range(self.tableStructure.columnCount()):
            if self.tableStructure.cellWidget(2, col).text() in ("PRI", "UNI"):
                unique = self.tableStructure.horizontalHeaderItem(col).text()
                uniqueCol = col
                break

        else:
            unique = self.tableStructure.horizontalHeaderItem(0).text()
            uniqueCol = 0

        self.Cursor.execute(f'SELECT * FROM `{database}`.`{table}`')

        databaseValues = {row: values for row, values in enumerate(self.Cursor.fetchall())}

        self.tableMessage.show()

        try:
            for row in range(self.tableData.rowCount()):
                uniqueValue = self.tableData.item(row, uniqueCol).text()

                if self.tableData.isRowHidden(row):
                    self.Cursor.execute(f"DELETE FROM `{database}`.`{table}` WHERE `{unique}` = %s", (uniqueValue,))

                    continue

                changedValues = []

                query = ""

                databaseRow = databaseValues.get(row)

                if databaseRow is None:
                    for col in range(self.tableData.columnCount()):
                        changedValues.append(self.tableData.item(row, col).text())
                        query += "%s, "

                    finalQuery = f"INSERT INTO `{database}`.`{table}` VALUES ({query[:-2]});"

                else:
                    for col in range(self.tableData.columnCount()):
                        value = self.tableData.item(row, col).text()

                        if value != databaseRow[col]:
                            changedValues.append(value)
                            query += f"`{self.tableStructure.horizontalHeaderItem(col).text()}` = %s, "

                    finalQuery = f"UPDATE `{database}`.`{table}` SET {query[:-2]} WHERE `{unique}` = '{uniqueValue}'"

                if query:
                    self.Cursor.execute(finalQuery, changedValues)

        except Error as error:
            self.tableMessage.setText(error.msg)

            return

        self.tableMessage.setText("Successfully Updated")
        self.tableData.resizeColumnsToContents()

        connection.commit()

    @Slot()
    def executeQuery(self, queries):
        if not queries.strip():
            return

        queries = queries.split(';')

        self.currentWidget.message.show()
        self.currentWidget.results.clear()

        try:
            count = 1

            for i, query in enumerate(queries):
                if not query.strip():
                    continue

                self.Cursor.execute(query)

                query = query.upper()

                if "USE" in query:
                    query = query.replace('`', '')

                    self.database.setText(f"Current Database: {query[4:]}")

                    flag = True

                elif any(clause in query for clause in ("SELECT", "SHOW", "EXPLAIN", "DESCRIBE", "DESC")):
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

                    self.currentWidget.results.addTab(table, f"Result - {count}")
                    self.currentWidget.results.show()

                    flag = False
                    count += 1

                elif any(clause in query for clause in ("ALTER", "CREATE", "DROP", "RENAME")):
                    self.refresh()

                    flag = i == 1

                else:
                    flag = i == 1

                if flag:
                    self.currentWidget.results.hide()

                self.currentWidget.message.setText("Successfully Executed")

        except Error as error:
            self.currentWidget.message.setText(error.msg)
            self.currentWidget.results.setHidden(not self.currentWidget.results.count())

    @Slot()
    def refresh(self):
        self.database.setText("Current Database:")
        self.databases.clear()
        self.table.setText("Current Table:")
        self.tableStructure.clear()
        self.tableData.clear()
        self.genDatabaseList()
        self.currentWidget.results.hide()
        self.currentWidget.message.hide()

        self.tableActions[2].setEnabled(False)
        self.tableActions[3].setEnabled(False)
        self.tableActions[4].setEnabled(False)

    @Slot()
    def openFile(self):
        if self.openFileDialog.exec() == QDialog.DialogCode.Rejected:
            return

        fileName = self.openFileDialog.selectedFiles()[0]

        if not fileName or fileName[-4:] != ".sql":
            return

        self.currentWidget.fileName = fileName
        self.currentWidget.file = open(self.currentWidget.fileName, "r+")
        self.currentWidget.fileContents = self.currentWidget.file.read()
        self.currentWidget.queryBox.setText(self.currentWidget.fileContents)

        self.queryTabs.setTabText(self.queryTabs.currentIndex(), fileName)

    @Slot()
    def saveFile(self):
        if self.currentWidget.file is None:
            if self.saveFileDialog.exec() == QDialog.DialogCode.Rejected:
                return

            fileName = self.saveFileDialog.selectedFiles()[0]

            if not fileName or fileName[-4:] != ".sql":
                return

            self.currentWidget.fileName = fileName
            self.currentWidget.file = open(self.currentWidget.fileName, "w+")
            self.queryTabs.setTabText(self.queryTabs.currentIndex(), fileName)

        self.currentWidget.file.truncate(0)
        self.currentWidget.file.seek(0)
        self.currentWidget.fileContents = self.currentWidget.queryBox.toPlainText()
        self.currentWidget.file.write(self.currentWidget.fileContents)
        self.currentWidget.file.flush()

        self.queryTabs.setTabText(self.queryTabs.currentIndex(), self.currentWidget.fileName)

    @Slot()
    def saveFileAs(self):
        if self.saveFileAsDialog.exec() == QDialog.DialogCode.Rejected:
            return

        fileName = self.saveFileAsDialog.selectedFiles()[0]

        if not fileName or fileName[-4:] != ".sql":
            return

        self.currentWidget.fileName = fileName

        if self.currentWidget.file is None:
            self.currentWidget.file = open(self.currentWidget.fileName, "w+")

        if self.currentWidget.fileName != self.currentWidget.file.name:
            self.currentWidget.file.close()
            self.currentWidget.file = open(self.currentWidget.fileName, "w+")

        self.currentWidget.file.truncate(0)
        self.currentWidget.file.seek(0)
        self.currentWidget.fileContents = self.currentWidget.queryBox.toPlainText()
        self.currentWidget.file.write(self.currentWidget.fileContents)
        self.currentWidget.file.flush()

        self.queryTabs.setTabText(self.queryTabs.currentIndex(), fileName)

    def closeEvent(self, event):
        changedFiles = []

        for index in range(self.queryTabs.count()):
            if self.queryTabs.tabText(index)[:2] == "* ":
                changedFiles.append(self.queryTabs.widget(index))

        if len(changedFiles):
            option = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save them?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if option == QMessageBox.StandardButton.Save:
                for file in changedFiles:
                    self.currentWidget = file
                    self.saveFile()

                event.accept()

            elif option == QMessageBox.StandardButton.Discard:
                event.accept()

            else:
                event.ignore()

        else:
            event.accept()


class QueryMode(QWidget):
    def __init__(self, parent: Window):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        self.parent = parent

        self.queryBox = QTextEdit()
        self.results = QTabWidget()
        self.message = QLabel()

        self.file = None
        self.fileName = ""
        self.fileContents = ""

        self.queryBox.textChanged.connect(self.check)

        self.layout().addWidget(self.queryBox)
        self.layout().addWidget(self.results)
        self.layout().addWidget(self.message)

        self.results.hide()
        self.message.hide()

    @Slot()
    def check(self):
        if self.file is None:
            return

        contents = self.queryBox.toPlainText()

        index = self.parent.queryTabs.currentIndex()

        if contents != self.fileContents:
            self.parent.queryTabs.setTabText(index, "* " + self.fileName)

        elif self.parent.queryTabs.tabText(index)[:2] == "* ":
            self.parent.queryTabs.setTabText(index, self.fileName)


class AddDatabaseWindow(QDialog):
    def __init__(self, parent: Window):
        super().__init__(parent)

        self.setWindowTitle("Add database")
        self.setLayout(QFormLayout())

        self.Cursor = parent.Cursor
        self.label = QLabel()
        entry = QLineEdit()
        button = QPushButton("Add")
        button.clicked.connect(lambda: self.add(entry.text()))

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), entry)
        self.layout().addRow(button)
        self.layout().addRow(self.label)

        self.label.hide()

    def add(self, database):
        self.Cursor.execute("SHOW DATABASES;")

        self.label.show()

        if (database,) in self.Cursor.fetchall():
            self.label.setText("Database already exists")
            return

        self.Cursor.execute(f"CREATE DATABASE `{database}`;")

        self.parent().databases.addTopLevelItem(QTreeWidgetItem((database,)))

        self.label.setText("Successfully Created")


class DropDatabaseWindow(QDialog):
    def __init__(self, parent: Window):
        super().__init__(parent)
        self.setLayout(QFormLayout())

        self.Cursor = parent.Cursor
        self.Cursor.execute("SHOW DATABASES;")

        databases = QComboBox()

        for (database,) in self.Cursor.fetchall():
            databases.addItem(database)

        databases.setCurrentIndex(-1)

        button = QPushButton("Drop")
        button.clicked.connect(lambda: self.drop(databases.currentText()))

        self.label = QLabel("Successfully Dropped")

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), databases)
        self.layout().addRow(button)
        self.layout().addRow(self.label)

        self.label.hide()

    def drop(self, database):
        self.Cursor.execute(f"DROP DATABASE `{database}`;")

        self.label.show()

        self.parent().refresh()


class DropTableWindow(QDialog):
    def __init__(self, parent: Window):
        super().__init__(parent)
        self.setLayout(QFormLayout())

        self.Cursor = parent.Cursor
        self.Cursor.execute("SHOW DATABASES;")

        databases = QComboBox()

        for (database,) in self.Cursor.fetchall():
            databases.addItem(database)

        databases.setCurrentIndex(-1)
        databases.currentTextChanged.connect(self.showTables)

        self.tables = QComboBox()

        button = QPushButton("Drop")
        button.clicked.connect(lambda: self.drop(databases.currentText(), self.tables.currentText()))

        self.label = QLabel("Successfully Dropped")

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Database:"), databases)
        self.layout().addRow(QLabel("Table:"), self.tables)
        self.layout().addRow(button)
        self.layout().addRow(self.label)

        self.label.hide()

    @Slot(str)
    def showTables(self, database):
        self.Cursor.execute(f"SHOW TABLES FROM `{database}`")

        for (table,) in self.Cursor.fetchall():
            self.tables.addItem(table)

        self.tables.setCurrentIndex(-1)

    def drop(self, database, table):
        self.Cursor.execute(f"DROP TABLE `{database}`.`{table}`;")

        self.label.show()

        self.parent().refresh()


class SessionManager(QMainWindow):
    def __init__(self):
        super().__init__(None)

        self.setWindowTitle("Session Manager")
        self.setCentralWidget(QWidget())

        self.message = QLabel()
        self.sessions = QTreeWidget()

        if isfile(sessionFile):
            with open(sessionFile, "rb") as file:
                self.data = load(file)

        else:
            self.data = {}

        self.sessionList = self.data.keys()

        for session in self.sessionList:
            self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

        self.sessions.setCurrentItem(None)

        self.host = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.connect = QPushButton("Connect")

        self.host.setMaxLength(15)
        self.host.setEnabled(False)
        self.user.setEnabled(False)
        self.password.setEnabled(False)
        self.connect.setEnabled(False)
        self.sessions.setHeaderHidden(True)

        self.connect.clicked.connect(self.openWindow)
        self.sessions.currentItemChanged.connect(self.showCredentials)

        self.menuBar().addAction("New Session", Qt.Modifier.CTRL | Qt.Key.Key_N, self.newSession)
        self.menuBar().addAction("Settings", Qt.Modifier.CTRL | Qt.Key.Key_I, lambda: SettingsPage(self).show())

        credentialLayout = QGridLayout()
        credentialLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credentialLayout.addWidget(QLabel("Host:"), 0, 0)
        credentialLayout.addWidget(self.host, 0, 1)
        credentialLayout.addWidget(QLabel("User:"), 1, 0)
        credentialLayout.addWidget(self.user, 1, 1)
        credentialLayout.addWidget(QLabel("Password:"), 2, 0)
        credentialLayout.addWidget(self.password, 2, 1)
        credentialLayout.addWidget(self.connect, 3, 0, 1, 2)
        credentialLayout.addWidget(self.message, 4, 0, 1, 2)

        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().addWidget(self.sessions)
        self.centralWidget().layout().addLayout(credentialLayout)

    @Slot(QTreeWidgetItem)
    def showCredentials(self, item):
        data = self.data.get(item.text(0))

        self.host.setEnabled(True)
        self.user.setEnabled(True)
        self.password.setEnabled(True)
        self.connect.setEnabled(True)

        self.host.setText(data.get("Host"))
        self.user.setText(data.get("User"))
        self.password.setText(data.get("Password"))

    @Slot()
    def newSession(self):
        session = f"Session - {len(self.sessionList) + 1}"
        self.data[session] = {}

        self.sessions.addTopLevelItem(QTreeWidgetItem((session,)))

    @Slot()
    def openWindow(self):
        global connection

        host = self.host.text()
        user = self.user.text()
        password = self.password.text()

        try:
            connection = connect(host=host, user=user, password=password)

        except Error as error:
            self.message.setText(error.msg)
            return

        self.data[self.sessions.currentItem().text(0)] = {"Host": host, "User": user, "Password": password}

        with open(sessionFile, "wb") as credentials:
            dump(self.data, credentials)

        self.close()

        Window().show()


class SettingsPage(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setLayout(QFormLayout())

        self.message = QLabel()
        self.theme = QComboBox()
        self.theme.addItems(QStyleFactory().keys())

        update = QPushButton("Update")
        update.clicked.connect(self.saveSettings)

        checkUpdates = QPushButton("Check for updates")
        checkUpdates.clicked.connect(lambda: Updater(self).updateProgram())

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.layout().addRow(QLabel("Theme:"), self.theme)
        self.layout().addRow(update)
        self.layout().addRow(self.message)
        self.layout().addRow(QLabel("Update Checker"))
        self.layout().addRow(checkUpdates)

        if isfile(configFile):
            with open(configFile, "rb") as file:
                app.setStyle(load(file).get("Theme"))

        self.theme.setCurrentText(app.style().name())
        self.theme.currentTextChanged.connect(lambda theme: app.setStyle(theme))

        self.message.hide()

    @Slot()
    def saveSettings(self):
        self.message.show()

        with open(configFile, "wb") as file:
            dump({"Theme": self.theme.currentText()}, file)

        self.message.setText("Changes will take place once you restart the application")


class Updater(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("MySQL Editor Updater")
        self.setLayout(QVBoxLayout())

        self.status = QLabel()
        self.layout().addWidget(self.status)

    def updateProgram(self):
        self.show()

        if not isdir(EXECUTABLE_PATH):
            mkdir(EXECUTABLE_PATH)

        try:
            request = get("https://api.github.com/repos/PandaRules/MySQL-Editor-Python/releases/latest")

        except ConnectionError:
            self.status.setText("No internet connection")
            return

        release = request.json()

        if not isfile(UPDATE_FILE):
            version = "v0.0.0.0"

        else:
            with open(UPDATE_FILE, "rb") as versionInfo:
                version = load(versionInfo).get("Version")

        for asset in release["assets"]:
            if asset["name"].replace('-', ' ') == EXECUTABLE_NAME and version != release["name"]:
                choice = QMessageBox.question(
                    self,
                    "MySQL Editor Updater",
                    "An update is available.\nWould you like to update?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if choice == QMessageBox.StandardButton.No:
                    self.close()
                    app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
                    return

                self.status.setText("Updating... please wait")
                self.status.repaint()
                progressBar = QProgressBar()
                self.layout().addWidget(progressBar)

                app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

                request = get(asset["url"], stream=True, headers={"Accept": "application/octet-stream"})
                request.raw.decode_content = True

                with open(EXECUTABLE_FILE, "wb") as executable:
                    totalSize = asset["size"]
                    size = 0

                    for chunk in request.iter_content(1024):
                        size += executable.write(chunk)
                        progressBar.setValue(size * 100 / totalSize)

                with open(UPDATE_FILE, "wb") as versionInfo:
                    dump({"Version": release["name"]}, versionInfo)

                self.status.setText("Successfully Updated!\nRestart for changes to take effect.")
                progressBar.hide()

                break

        else:
            self.status.setText("No update found")


if __name__ == '__main__':
    app = QApplication()

    if platform != "linux":
        unsupported = QLabel("This is the configurator for Linux systems")
        unsupported.show()

        exit(app.exec())

    cwd = getcwd()

    if EXECUTABLE_PATH != cwd:
        EXECUTABLE_PATH = cwd
        CONFIG_PATH = cwd
        EXECUTABLE_FILE = join(cwd, EXECUTABLE_NAME)

    if not isdir(CONFIG_PATH):
        mkdir(CONFIG_PATH)

    configFile = join(CONFIG_PATH, "config.dat")
    sessionFile = join(CONFIG_PATH, "sessions.dat")

    if isfile(configFile):
        with open(configFile, "rb") as file:
            app.setStyle(load(file).get("Theme"))

    SessionManager().show()

    exit(app.exec())
