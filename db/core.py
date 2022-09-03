"""
Module implements base class for databases
"""


import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from common.config import settings
from common.exceptions import NotExist


class DatabaseFactory:
    """
    Factory class. For auto database connection initialization
    """
    class Database(BaseModel):
        dialect: str
        driver: str
        user: Optional[str]
        password: Optional[str]
        host: Optional[str]
        port: Optional[str]
        name: str

        def get_src(self, client: str = None) -> str:
            path = Path(__file__).resolve().parent.parent
            if client:
                return f'sqlite+pysqlite:///{path}/client/{client}_database.sqlite3'

            if self.dialect == 'sqlite':
                return f'sqlite+pysqlite:///{path}/server/{self.name}'
            else:
                return f'{self.dialect}+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'

    def __init__(self, classname: str, client: str = None):
        self.__client = client
        self.__name = settings.DATABASE
        self.kind = classname
        if self.kind == 'ClientDatabase':
            self.__name = 'client'
        self.__get_db_creds()

    def __get_db_creds(self):
        """
        collect database credentials from config file and set it into {__creds} variable
        :return: None
        """
        path = Path(__file__).resolve().parent
        with open(f'{path}/config.json', 'r', encoding='utf-8') as f:
            databases = json.load(f)
        self.__creds = self.Database.parse_obj(databases[self.kind][self.__name])

    def get_engine(self) -> Engine:
        """
        takes engine source from {__creds} and creates SQLAlchemy Engine object
        :return: Engine
        """
        if self.__creds.dialect == 'sqlite':
            return create_engine(self.__creds.get_src(self.__client), connect_args={"check_same_thread": False})
        return create_engine(self.__creds.get_src())


class Database:
    """
    Databases base class.
    """

    def __init__(self, client: str = None):
        self._db = self._connect(client)

    @staticmethod
    def _create_tables(engine: Engine):
        raise NotImplementedError

    def _get_database(self, client: str) -> Engine:
        """
        Return engine instance
        :param client: str - need only for client database handler creation
        :return: sqlalchemy.Engine
        """

        factory = DatabaseFactory(self.__class__.__name__, client)
        return factory.get_engine()

    def _connect(self, client: str) -> Session:
        """
        Return session instance
        :param client: str - need only for client database handler creation
        :return: sqlalchemy.orm.Session
        """

        engine = self._get_database(client)
        db_init = self._create_tables(engine)
        if db_init:
            return Session(bind=engine)
        raise NotExist("Database creation error")

    def __del__(self):
        if hasattr(self, '_db'):
            self._db.close()
