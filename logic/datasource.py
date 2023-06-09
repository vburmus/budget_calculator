import os

import pyodbc
from loguru import logger


class DataSource:
    __instance = None

    def __init__(self):
        logger.add("logs/application.log", rotation="500 MB", level="INFO")
        if DataSource.__instance is not None:
            raise Exception("Singleton class, use get_instance() to obtain an instance.")
        self.connection = pyodbc.connect(
            driver="{MySQL ODBC 8.0 ANSI Driver}",
            server=os.environ.get("SERVER_PATH"),
            user="root",
            password="root",
            database="mydb",
            autocommit=True
        )
        logger.info("DataSource created, connection made.")

    @staticmethod
    def get_instance():
        if DataSource.__instance is None:
            DataSource.__instance = DataSource()
        return DataSource.__instance

    @staticmethod
    def get_connection():
        return DataSource.get_instance().connection
