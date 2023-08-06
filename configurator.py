from os import getenv, listdir, mkdir, remove, removedirs, system
from os.path import isdir, isfile, join
from pickle import dump
from sys import platform, exit

from PySide6.QtCore import QEventLoop, Slot
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QLabel, QMainWindow, QProgressBar, QPushButton, QVBoxLayout,
    QWidget
)
from requests import get
from requests.exceptions import ConnectionError

EXECUTABLE_NAME = "MySQL Editor.bin"
CONFIGURATOR_NAME = "MySQL Editor Configurator.bin"
EXECUTABLE_PATH = join(getenv("HOME"), ".local", "share", "MySQL Editor")
EXECUTABLE_FILE = join(EXECUTABLE_PATH, EXECUTABLE_NAME)
CONFIGURATOR_FILE = join(EXECUTABLE_PATH, CONFIGURATOR_NAME)
CONFIG_PATH = join(getenv("HOME"), ".config", "MySQL Editor")
UPDATE_FILE = join(CONFIG_PATH, "update.dat")


@Slot()
def install():
    installer = QDialog(configurator)
    installer.setWindowTitle("MySQL Editor Installer")
    installer.show()

    status = QLabel()

    installer.setLayout(QVBoxLayout())
    installer.layout().addWidget(status)

    status.show()

    if not isdir(EXECUTABLE_PATH):
        mkdir(EXECUTABLE_PATH)

    try:
        request = get("https://api.github.com/repos/PandaRules/MySQL-Editor-Python/releases/latest")

    except ConnectionError:
        status.setText("No internet connection")

        return

    release = request.json()

    noRelease = True

    progressBar = QProgressBar()
    installer.layout().addWidget(progressBar)

    for asset in release["assets"]:
        if asset["name"].replace('-', ' ') == EXECUTABLE_NAME:
            file = EXECUTABLE_FILE

        elif asset["name"].replace('-', ' ') == CONFIGURATOR_NAME:
            file = CONFIGURATOR_FILE

        else:
            continue

        status.setText(f"Installing {asset['name'][:-4]}... please wait")
        status.repaint()

        app.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

        while True:
            try:
                request = get(asset["url"], stream=True, headers={"Accept": "application/octet-stream"})

                break

            except ConnectionError:
                continue

        request.raw.decode_content = True

        with open(file, "wb") as executable:
            totalSize = asset["size"]
            size = 0

            for chunk in request.iter_content(1024):
                size += executable.write(chunk)
                progressBar.setValue(size * 100 / totalSize)

        noRelease = False

    if noRelease:
        status.setText("No suitable release found")

        return

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

    with open(UPDATE_FILE, "wb") as versionInfo:
        dump({"Version": release["tag_name"]}, versionInfo)

    status.setText("Successfully installed!")
    progressBar.hide()


@Slot()
def uninstall():
    uninstaller = QDialog(configurator)
    uninstaller.setWindowTitle("MySQL Editor Uninstaller")
    uninstaller.show()

    status = QLabel()

    uninstaller.setLayout(QVBoxLayout())
    uninstaller.layout().addWidget(status)

    installed = False

    if isdir(EXECUTABLE_PATH):
        for file in listdir(EXECUTABLE_PATH):
            remove(join(EXECUTABLE_PATH, file))

        removedirs(EXECUTABLE_PATH)
        installed = True

    desktopPath = join(getenv("HOME"), ".local", "share", "applications")

    executableShortcut = join(desktopPath, "MySQL Editor.desktop")
    configuratorShortcut = join(desktopPath, "MySQL Editor Configurator.desktop")

    if isfile(executableShortcut):
        remove(executableShortcut)
        installed = True

    if isfile(configuratorShortcut):
        remove(configuratorShortcut)
        installed = True

    status.show()
    status.setText("Successfully uninstalled" if installed else "MySQL Editor is not installed")


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

    installButton.clicked.connect(install)
    uninstallButton.clicked.connect(uninstall)

    centralWidget = QWidget()
    centralWidget.setLayout(QFormLayout())
    centralWidget.layout().addRow(installButton)
    centralWidget.layout().addRow(uninstallButton)

    configurator.setCentralWidget(centralWidget)
    configurator.show()

    exit(app.exec())
