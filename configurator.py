from os import mkdir, remove, removedirs
from os.path import isdir
from pickle import dump
from sys import platform, exit

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QLabel, QMainWindow, QProgressBar, QPushButton, QVBoxLayout,
    QWidget
)
from requests import get


class Installer(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("MySQL Editor Installer")
        self.setLayout(QVBoxLayout())

        self.status = QLabel()
        self.layout().addWidget(self.status)

    def install(self):
        self.show()

        if not isdir(executablePath):
            mkdir(executablePath)

        request = get("https://api.github.com/repos/PandaRules/MySQL-Editor-Python/releases/latest")
        release = request.json()

        noRelease = True

        progressBar = QProgressBar()

        for asset in release["assets"]:
            if asset["name"].replace('-', ' ') == executableName:
                file = executableFile

            elif asset["name"].replace('-', ' ') == configuratorName:
                file = configuratorFile

            else:
                continue

            progressBar.setValue(0)
            self.status.setText(f"Installing {asset['name'][:-4]}... please wait")
            self.status.repaint()
            self.layout().addWidget(progressBar)

            app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

            request = get(asset["url"], stream=True, headers={"Accept": "application/octet-stream"})
            request.raw.decode_content = True

            with open(file, "wb") as executable:
                totalSize = asset["size"]
                size = 0

                for chunk in request.iter_content(1024):
                    size += executable.write(chunk)
                    progressBar.setValue(size * 100 / totalSize)

            createShortcut()

            noRelease = False

        if noRelease:
            self.status.setText("No suitable release found")

        else:
            with open(updateFile, "wb") as versionInfo:
                dump({"Version": release["name"]}, versionInfo)

            self.status.setText("Successfully installed!")
            progressBar.hide()


class Uninstaller(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("MySQL Editor Uninstaller")
        self.setLayout(QVBoxLayout())

        self.status = QLabel()
        self.layout().addWidget(self.status)

    def uninstall(self):
        self.show()

        if not isdir(executablePath):
            self.status.setText("MySQL Editor is not installed")
            return

        remove(executableFile)
        removedirs(executablePath)
        removeShortcut()

        self.status.setText("Successfully uninstalled")


if __name__ == '__main__':
    app = QApplication()

    if platform == "win32":
        from windows import (createShortcut, configuratorFile, configuratorName, executableFile, executableName,
                             executablePath, removeShortcut, updateFile)

    elif platform == "linux":
        from linux import (createShortcut, configuratorFile, configuratorName, executableFile, executableName,
                           executablePath, removeShortcut, updateFile)

    else:
        unsupported = QLabel("Only Windows and Linux are supported")
        unsupported.show()

        exit(app.exec())

    configurator = QMainWindow()
    configurator.setWindowTitle("MySQL Editor Configurator")

    installButton = QPushButton("Install MySQL Editor")
    uninstallButton = QPushButton("Uninstall MySQL Editor")

    installButton.clicked.connect(lambda: Installer(configurator).install())
    uninstallButton.clicked.connect(lambda: Uninstaller(configurator).uninstall())

    centralWidget = QWidget()
    centralWidget.setLayout(QFormLayout())
    centralWidget.layout().addRow(installButton)
    centralWidget.layout().addRow(uninstallButton)

    configurator.setCentralWidget(centralWidget)
    configurator.show()

    exit(app.exec())
