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