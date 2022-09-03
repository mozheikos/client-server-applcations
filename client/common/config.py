"""
Gets all application settings from config.json
"""


import json
import os
from enum import Enum

from pydantic import BaseModel


class Settings(BaseModel):
    class Status(str, Enum):
        ok = '200 OK'
        bad_request = '400 Bad Request'
        forbidden = '403 Forbidden'
        unauthorized = '401 Unauthorized'

    class Action(str, Enum):
        probe = 'probe'
        presence = 'presence'
        register = 'register'
        auth = 'authenticate'
        quit = 'quit'
        join = 'join'
        leave = 'leave'
        msg = 'msg'
        recv = 'recv'
        server_shutdown = 'server_shutdown'
        contacts = 'contacts'
        search = 'search'
        add_chat = 'add_chat'
        del_chat = 'del_chat'
        messages = 'messages'

    def __init__(self):
        super(Settings, self).__init__()
        path = os.getcwd()
        with open(f'{path}/common/config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.__set_attributes(data)

    def __set_attributes(self, data: dict):
        """
        Takes data from config.json and implement class variables same as field names in json
        :param data: dict - json loaded data from config.json
        :return:
        """

        for k, v in data.items():
            self.__dict__[k] = v


settings = Settings()
