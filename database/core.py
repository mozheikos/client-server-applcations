import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base

from common.config import settings

Base = declarative_base()


class DatabaseFactory:

    class Database(BaseModel):
        dialect: str
        driver: str
        user: Optional[str]
        password: Optional[str]
        host: Optional[str]
        port: Optional[str]
        name: str

        def get_src(self) -> str:
            if self.dialect == 'sqlite':
                path = Path(__file__).resolve().parent
                return f'sqlite+{self.driver}:///{path}/{self.name}'
            else:
                return f'{self.dialect}+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'

    def __init__(self):
        self.__name = settings.DATABASE
        self.__get_db_creds()

    def __get_db_creds(self):
        """
        collect database credentials from config file and set it into {__creds} variable
        :return: None
        """
        path = Path(__file__).resolve().parent
        with open(f'{path}/config.json', 'r', encoding='utf-8') as f:
            databases = json.load(f)
        self.__creds = self.Database.parse_obj(databases[self.__name])

    def get_engine(self) -> Engine:
        """
        takes engine source from {__creds} and creates SQLAlchemy Engine object
        :return: Engine
        """
        return create_engine(self.__creds.get_src())
