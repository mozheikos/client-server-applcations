import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from common.config import settings


class DatabaseFactory:

    class Database(BaseModel):
        dialect: str
        driver: str
        user: Optional[str]
        password: Optional[str]
        host: Optional[str]
        port: Optional[str]
        name: str

        def get_src(self, client: str = None) -> str:
            if client:
                return f'sqlite+pysqlite:///{client}_database.sqlite3'

            if self.dialect == 'sqlite':
                path = Path(__file__).resolve().parent
                return f'sqlite+{self.driver}:///{path}/{self.name}'
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
