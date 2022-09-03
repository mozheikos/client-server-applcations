"""
Module to definition data models
"""


from socket import socket
from typing import Optional, Union, List, Deque

from pydantic import BaseModel

from common.config import settings


class Base(BaseModel):
    """
    Implementation Base class to use config of data validation
    """
    class Config:
        arbitrary_types_allowed = True
        max_anystr_length = 1200
        error_msg_templates = {
            'value_error.any_str.max_length': 'max length: {limit_value}'
        }


class User(Base):
    """
    Represents user
    """

    id: Optional[int]
    login: str
    password: Optional[str]
    verbose_name: Optional[str]
    token: Optional[str]


class Message(Base):
    """
    Represents message
    """

    to: str
    from_: str
    encoding: str = 'utf-8'
    message: str
    date: Optional[str]


class Request(Base):
    """
    Represents request
    """

    status: Optional[settings.Status]
    action: settings.Action
    time: str
    type: Optional[str]
    user: Optional[User]
    data: Optional[Union[Message, User, str, List[User], List[Message], List[int]]]


class ConnectedUser(Base):
    """
    Represents client, connected to server
    """
    user: User
    sock: socket
    data: Deque[Union[str, Request]]
    token: str
