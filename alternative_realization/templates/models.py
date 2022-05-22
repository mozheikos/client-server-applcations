import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field

"""Здесь я подключаю pydantic и создаю модели. Пока это выглядит излишним, но в итоге, когда добавится
работа с базой данных и прочие усложнения - уверен, это здорово облегчит жизнь и сделает код аккуратнее и короче"""


class Message(BaseModel):
    to: str
    from_: str = Field(alias='from')
    encoding: str = 'ascii'
    message: str


class User(BaseModel):
    account_name: str
    password: Optional[str]
    status: Optional[str]


class Request(BaseModel):
    action: str
    time: datetime.datetime
    type: Optional[str]
    user: User
    data: Optional[Union[str, Message]]


class Response(BaseModel):
    response: int
    time: datetime.datetime
    alert: Optional[str]
    error: Optional[str]
