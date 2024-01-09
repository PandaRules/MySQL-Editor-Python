# Version 2024.01.09.1

+ Switched to a new versioning system of `yyyy.mm.dd.version`

## Backend (no change in functionality)

+ Switched to QSettings from configparser


+ [add_database.py](src/mysql_editor/add_database.py)
    + Renamed variables
    + Made AddDatabaseWindow.add() a Slot()


+ [query.py](src/mysql_editor/query.py)
    + Renamed variables and methods
    + Edited type annotations


+ [session.py](src/mysql_editor/session.py)
    + Renamed variables and methods
    + Update algorithm for renaming a session
    + Reordered methods


+ [window.py](src/mysql_editor/window.py)
    + Renamed variables and methods
    + Edited type annotations
    + Made table structure and table data their own classes in table_structure_view.py and table_data_view.py
      respectively
    + Reformatted several parts

## Frontend (functionality changes)

+ [session.py](src/mysql_editor/session.py)
    + Made it possible to rename sessions by double-clicking the entry


+ [window.py](src/mysql_editor/window.py)
    + Made it possible to rename tables by double-clicking the entry
    + Added a menu for added and dropping databases and dropping tables
    + Consequently removed those respective buttons
    + Made the table data detect datetime

# Version 1.0.4

+ Lowered minimum requirements
    + As a result, Python 3.7 and above are now supported!

# Version 1.0.3

+ Bug fixes
    + Fixed a bug which prevented deletion of a row from a table
    + Made it possible to not edit write-protected databases
    + Fixed a bug regarding numbering of new sessions and query tabs
    + Fixed a bug where credentials were not cleared when deleting a session
    + Fixed more bugs


+ Made it possible to rename sessions


+ Switched to QListWidget for session manager


+ Optimized session creation


+ Redesigned the UI of the main window slightly

# Version 1.0.2.1

+ Fixed a typo in [README](README.md)


+ Fixed a bug in [window.py](src/mysql_editor/window.py)

# Version 1.0.2

+ Updated [README](README.md)


+ Removed `requests` as a dependency


+ Added a changelog


+ \_\_init\_\_.py
    + Removed


+ [add_database.py](src/mysql_editor/add_database.py)
    + Minor Formatting changes


+ drop_database.py
    + Removed


+ drop_table.py
    + Removed


+ [files.py](src/mysql_editor/files.py)
    + Removed a redundant check


+ [session.py](src/mysql_editor/session.py)
    + Minor Formatting changes
    + Fixed a bug where Remove Session could be pressed when no session was selected


+ [window.py](src/mysql_editor/window.py)
    + Reworked the saving algorithm
    + Redid some of the UI
    + Reworked the closing changes algorithm

# Version 1.0.1

+ Updated [README](README.md)

# Version 1.0.0

+ Initial Release
