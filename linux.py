from os.path import join, isdir
from os import getenv, mkdir, system, remove


def createShortcut():
    desktopPath = join(getenv("HOME"), ".local", "share", "applications")

    if not isdir(desktopPath):
        mkdir(desktopPath)

    with open(join(desktopPath, "MySQL Editor.desktop"), "w") as shortcut:
        shortcut.writelines([
            "[Desktop Entry]\n",
            "Comment=Tool for viewing and editing MySQL Databases\n",
            f"Exec='{executableFile}'\n",
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
            f"Exec='{configuratorFile}'\n",
            "Keywords=SQL;\n",
            "Name=MySQL Editor Configurator\n",
            "NoDisplay=false\n",
            "StartupNotify=true\n",
            "Terminal=false\n",
            "Type=Application\n"
        ])

    system(f"chmod +x '{executableFile}'")
    system(f"chmod +x '{configuratorFile}'")


def removeShortcut():
    desktopPath = join(getenv("HOME"), ".local", "share", "applications")

    if not isdir(desktopPath):
        return

    remove(join(desktopPath, "MySQL Editor.desktop"))
    remove(join(desktopPath, "MySQL Editor Configurator.desktop"))


executableName = "MySQL Editor.bin"
configuratorName = "MySQL Editor Configurator.bin"
executablePath = join(getenv("HOME"), ".local", "share", "MySQL Editor")
executableFile = join(executablePath, executableName)
configuratorFile = join(executablePath, configuratorName)
configPath = join(getenv("HOME"), ".config", "MySQL Editor")
updateFile = join(configPath, "update.dat")
