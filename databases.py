import datetime
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from common.config import settings
from common.utils import get_hashed_password
from database.core import DatabaseFactory
from database.server_models import MessageHistory, Client, ClientHistory, create_tables
from exceptions import UserNotExist, UserAlreadyExist, DatabaseNotExist
from templates.templates import Message, User


class Database:

    def __init__(self):
        self._db = self._connect()

    @staticmethod
    def _get_database() -> Engine:
        factory = DatabaseFactory()
        return factory.get_engine()

    def _connect(self) -> Session:
        engine = self._get_database()
        db_init = create_tables(engine)
        if db_init:
            return Session(bind=engine)
        raise DatabaseNotExist("Database creation error")
        
    def __del__(self):
        self._db.close()


class ServerDatabase(Database):

    def __init__(self):
        super(ServerDatabase, self).__init__()

    def get_user(self, username: str) -> Optional[Client]:
        user: Client = self._db.query(Client).filter(Client.login == username).one_or_none()
        return user

    def create_user(self, user: User, ip: str) -> int:
        if self.get_user(user.login):
            raise UserAlreadyExist(f'Пользователь <{user.login}> уже существует')

        assert user.password, "Необходимо задать пароль"

        password = get_hashed_password(user.password)
        client = Client(
            login=user.login,
            password=password,
            verbose_name=user.verbose_name if user.verbose_name else f"@{user.login}",
            created_at=datetime.datetime.now()
        )
        connected = ClientHistory(
            client=client,
            date=datetime.datetime.now(),
            address=ip
        )

        self._db.add(connected)
        self._db.commit()

        return client.id

    def get_user_contact_list(self, user: User) -> List[str]:
        pk = self._db.query(Client.id).filter(Client.login == user.login).scalar()

        sent = self._db.query(Client.login).join(MessageHistory, MessageHistory.recipient_id == Client.id).filter(
            MessageHistory.sender_id == pk
        ).all()

        receive = self._db.query(Client.login).join(MessageHistory, MessageHistory.sender_id == Client.id).filter(
            MessageHistory.recipient_id == pk
        ).all()

        result = [x[0] for x in sent + receive]
        return result

    def get_message_history(self, user: str, recipient: str) -> List[Message]:

        messages: List[MessageHistory] = self._db.query(MessageHistory).filter(
            or_(
                MessageHistory.sender.login == user,
                MessageHistory.recipient.login == user
            )
        ).filter(
            or_(
                MessageHistory.sender.login == recipient,
                MessageHistory.recipient.login == recipient
            )
        ).all()

        result = [Message(
            to=x.recipient.login,
            from_=x.sender.login,
            message=x.content,
            date=x.date.strftime(settings.DATE_FORMAT)
        ) for x in messages]

        return result

    def create_message(self, data: Message):
        sender = self.get_user(data.from_)
        if not sender:
            raise UserNotExist(f"Пользователь {data.from_} не существует")

        recipient = self.get_user(data.to)
        if not recipient:
            raise UserNotExist(f"Пользователь {data.from_} не существует")

        message = MessageHistory(
            date=datetime.datetime.strptime(data.date, settings.DATE_FORMAT),
            content=data.message,
            sender=sender,
            recipient=recipient
        )
        self._db.add(message)
        self._db.commit()
