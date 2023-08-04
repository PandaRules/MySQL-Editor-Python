from os.path import join, isdir
from os import mkdir, getenv, remove, removedirs


def createShortcut():
    startMenuPath = join(getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "MySQL Editor")

    if not isdir(startMenuPath):
        mkdir(startMenuPath)

    from win32com.client import Dispatch

    shell = Dispatch("WScript.shell")

    appShortcut = shell.CreateShortCut(join(startMenuPath, "MySQL Editor.lnk"))
    appShortcut.TargetPath = executableFile
    appShortcut.save()

    configuratorShortcut = shell.CreateShortCut(join(startMenuPath, "MySQL Editor Configurator.lnk"))
    configuratorShortcut.TargetPath = configuratorFile
    configuratorShortcut.save()


def removeShortcut():
    startMenuPath = join(getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "MySQL Editor")

    if not isdir(startMenuPath):
        return

    remove(join(startMenuPath, "MySQL Editor.lnk"))
    remove(join(startMenuPath, "MySQL Editor Configurator.lnk"))
    removedirs(startMenuPath)


executableName = "MySQL Editor.exe"
configuratorName = "MySQL Editor Configurator.exe"
executablePath = join(getenv("APPDATA"), "MySQL Editor")
executableFile = join(executablePath, executableName)
configuratorFile = join(executablePath, configuratorName)
configPath = join(getenv("LOCALAPPDATA"), "MySQL Editor")
updateFile = join(configPath, "update.dat")
