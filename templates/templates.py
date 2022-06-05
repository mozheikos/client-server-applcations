from typing import Optional, Union
from pydantic import BaseModel

from common.config import Action, Status


class Base(BaseModel):
    class Config:
        max_anystr_length = 300
        error_msg_templates = {
            'value_error.any_str.max_length': 'max length: {limit_value}'
        }


class Message(Base):
    to: str
    from_: str
    encoding: str = 'utf-8'
    message: str


class User(Base):
    account_name: str
    password: Optional[str]
    status: Optional[str]


class Request(Base):
    action: Action
    time: str
    type: Optional[str]
    user: Optional[User]
    data: Optional[Union[str, Message]]


class Response(Base):
    response: Status
    time: str
    alert: Optional[str]
    error: Optional[str]
