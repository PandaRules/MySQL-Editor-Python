from io import TextIOWrapper
from typing import Optional


class File:
    def __init__(self):
        self.name: str = ""
        self.file: Optional[TextIOWrapper] = None
        self.contents: str = ""

    def open(self, name: str, mode: str):
        if self.file is not None and not self.file.closed:
            self.file.close()

        self.name = name
        self.file = open(name, mode)

        if "r" in mode:
            self.contents = self.file.read()

    def save(self, content: str):
        self.file.truncate(0)
        self.file.seek(0)
        self.contents = content
        self.file.write(content)
        self.file.flush()
