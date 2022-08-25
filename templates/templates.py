from typing import Optional, Union, List, Deque
from socket import socket

from pydantic import BaseModel

from common.config import settings


class Base(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        max_anystr_length = 300
        error_msg_templates = {
            'value_error.any_str.max_length': 'max length: {limit_value}'
        }


class Message(Base):
    to: str
    from_: str
    encoding: str = 'utf-8'
    message: str
    date: Optional[str]


class User(Base):
    id: Optional[int]
    login: str
    password: Optional[str]
    verbose_name: Optional[str]


class Response(Base):
    response: settings.Status
    # action: settings.Action
    # time: str
    alert: Optional[Union[int, str]]


class Request(Base):
    status: Optional[settings.Status]
    action: settings.Action
    time: str
    type: Optional[str]
    user: Optional[User]
    data: Optional[Union[Message, User, str, List[User]]]


# Пользовательский сокет сохраняю в виде списка, чтобы (ТЕОРЕТИЧЕСКИ) можно было подключиться с 2 устройств к одному
# аккаунту (пока пароль проверять не буду, но будет база - по паролю и будем решать: добавлять новый сокет в список или
# это нарушитель
class ConnectedUser(Base):
    user: User
    sock: List[socket]
    data: Deque[Union[str, Request]]
    