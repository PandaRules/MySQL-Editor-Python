from typing import Any, Iterable, List, Optional, Self, Tuple, Union

from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import Error


class Backend:
    __cursor: Optional[MySQLCursor] = None
    __instance: Optional[Self] = None

    def __new__(cls, connection: Optional[MySQLConnection] = None):
        if cls.__instance is None:
            cls.__instance = super(Backend, cls).__new__(cls)
            cls.__instance.__cursor = connection.cursor()

        return cls.__instance

    def getDatabases(self) -> List[str]:
        self.__cursor.execute("SHOW DATABASES;")

        return self.__cursor.fetchall()

    def getTables(self, database: str, tableType: str) -> List[str]:
        self.__cursor.execute(f"SHOW FULL TABLES IN `{database}` WHERE TABLE_TYPE LIKE '{tableType}';")

        return self.__cursor.fetchall()

    def getTableStructure(self, database: str, table: str) -> Tuple[List[Tuple[Any]], Tuple[str]]:
        self.__cursor.execute(f"DESC `{database}`.`{table}`;")

        return self.__cursor.fetchall(), self.__cursor.column_names

    def getData(self, database: str, table: str) -> Tuple[List[Tuple[Any]], Tuple[str]]:
        self.__cursor.execute(f"SELECT * FROM `{database}`.`{table}`;")

        return self.__cursor.fetchall(), self.__cursor.column_names

    def setDatabase(self, database: str) -> None:
        self.__cursor.execute(f"USE `{database}`;")

    def addDatabase(self, database: str) -> Optional[Error]:
        try:
            self.__cursor.execute(f"CREATE DATABASE `{database}`;")

        except Error as error:
            return error

        return None

    def dropDatabase(self, database: str) -> Optional[Error]:
        try:
            self.__cursor.execute(f"DROP DATABASE `{database}`;")

        except Error as error:
            return error

        return None

    def dropTable(self, database: str, table: str) -> Optional[Error]:
        try:
            self.__cursor.execute(f"DROP TABLE `{database}`.`{table}`;")

        except Error as error:
            return error

        return None

    def renameTable(self, database: str, old: str, new: str) -> Optional[Error]:
        try:
            self.__cursor.execute(f"RENAME TABLE `{database}`.`{old}` TO `{database}`.`{new}`;")

        except Error as error:
            return error

        return None

    def executeQuery(self, query: str) -> Union[Error, Tuple[List[Tuple[Any]], List[str]]]:
        try:
            self.__cursor.execute(query)

        except Error as error:
            return error

        return self.__cursor.fetchall(), self.__cursor.column_names

    def executeQueries(self, queries: List[str], parameters: List[Iterable]) -> Optional[Error]:
        try:
            for query, parameter in zip(queries, parameters):
                self.__cursor.execute(query, parameter)

        except Error as error:
            return error

        return None
