from os import getenv, mkdir, remove, removedirs, system
from os.path import isdir, join
from pickle import dump
from sys import platform, exit

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QLabel, QMainWindow, QProgressBar, QPushButton, QVBoxLayout,
    QWidget
)
from requests import get

EXECUTABLE_NAME = "MySQL Editor.bin"
CONFIGURATOR_NAME = "MySQL Editor Configurator.bin"
EXECUTABLE_PATH = join(getenv("HOME"), ".local", "share", "MySQL Editor")
EXECUTABLE_FILE = join(EXECUTABLE_PATH, EXECUTABLE_NAME)
CONFIGURATOR_FILE = join(EXECUTABLE_PATH, CONFIGURATOR_NAME)
CONFIG_PATH = join(getenv("HOME"), ".config", "MySQL Editor")
UPDATE_FILE = join(CONFIG_PATH, "update.dat")


def createShortcut():
    desktopPath = join(getenv("HOME"), ".local", "share", "applications")

    if not isdir(desktopPath):
        mkdir(desktopPath)

    with open(join(desktopPath, "MySQL Editor.desktop"), "w") as shortcut:
        shortcut.writelines([
            "[Desktop Entry]\n",
            "Comment=Tool for viewing and editing MySQL Databases\n",
            f"Exec='{EXECUTABLE_FILE}'\n",
            "GenericName=SQL Editor\n",
            "Keywords=SQL;\n",
            "Name=MySQL Editor\n",
            "NoDisplay=false\n",
            "StartupNotify=true\n",
            "Terminal=false\n",
            "Type=Application\n"
        ])

    with open(join(desktopPath, "MySQL Editor Configurator.desktop"), "w") as shortcut:
        shortcut.writelines([
            "[Desktop Entry]\n",
            "Comment=Configurator for MySQL Editor\n",
            f"Exec='{CONFIGURATOR_FILE}'\n",
            "Keywords=SQL;\n",
            "Name=MySQL Editor Configurator\n",
            "NoDisplay=false\n",
            "StartupNotify=true\n",
            "Terminal=false\n",
            "Type=Application\n"
        ])

    system(f"chmod +x '{EXECUTABLE_FILE}'")
    system(f"chmod +x '{CONFIGURATOR_FILE}'")


def removeShortcut():
    desktopPath = join(getenv("HOME"), ".local", "share", "applications")

    if not isdir(desktopPath):
        return

    remove(join(desktopPath, "MySQL Editor.desktop"))
    remove(join(desktopPath, "MySQL Editor Configurator.desktop"))


class Installer(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("MySQL Editor Installer")
        self.setLayout(QVBoxLayout())

        self.status = QLabel()
        self.layout().addWidget(self.status)

    def install(self):
        self.show()

        if not isdir(EXECUTABLE_PATH):
            mkdir(EXECUTABLE_PATH)

        request = get("https://api.github.com/repos/PandaRules/MySQL-Editor-Python/releases/latest")
        release = request.json()

        noRelease = True

        progressBar = QProgressBar()

        for asset in release["assets"]:
            if asset["name"].replace('-', ' ') == EXECUTABLE_NAME:
                file = EXECUTABLE_FILE

            elif asset["name"].replace('-', ' ') == CONFIGURATOR_NAME:
                file = CONFIGURATOR_FILE

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
            with open(UPDATE_FILE, "wb") as versionInfo:
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

        if not isdir(EXECUTABLE_PATH):
            self.status.setText("MySQL Editor is not installed")
            return

        remove(EXECUTABLE_FILE)
        removedirs(EXECUTABLE_PATH)
        removeShortcut()

        self.status.setText("Successfully uninstalled")


if __name__ == '__main__':
    app = QApplication()

    if platform != "linux":
        unsupported = QLabel("This is the configurator for Linux systems")
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
