import datetime
from typing import Optional, List

from sqlalchemy import or_, and_
from sqlalchemy.engine import Engine

from common.config import settings
from common.exceptions import AlreadyExist, NotExist
from common.utils import get_hashed_password
from db.core import Database
from server.models import Client, create_tables, ClientHistory, Chat, MessageHistory
from templates.templates import User, Message


class ServerDatabase(Database):

    def __init__(self):
        super(ServerDatabase, self).__init__()

    @staticmethod
    def _create_tables(engine: Engine):
        return create_tables(engine)

    def get_user(self, username: str) -> Optional[Client]:
        user: Client = self._db.query(Client).filter(Client.login == username).one_or_none()
        return user

    def search(self, value: str) -> List[User]:
        users = self._db.query(Client).filter(Client.login.like(value)).all()

        return [User(
            id=x.id, login=x.login, verbose_name=x.verbose_name
        ) for x in users]

    def auth_user(self, user: Client, ip: str):
        connected = ClientHistory(
            client=user,
            date=datetime.datetime.now(),
            address=ip
        )
        self._db.add(connected)
        self._db.commit()

    def create_user(self, user: User) -> int:
        if self.get_user(user.login):
            raise AlreadyExist(f'Пользователь <{user.login}> уже существует')

        assert user.password, "Необходимо задать пароль"

        password = get_hashed_password(user.password)
        client = Client(
            login=user.login,
            password=password,
            verbose_name=user.verbose_name if user.verbose_name else f"@{user.login}",
            created_at=datetime.datetime.now()
        )

        self._db.add(client)
        self._db.commit()

        return client.id

    def get_user_contact_list(self, user: User) -> List[Client]:

        contacts: List[Chat] = self._db.query(Chat).filter(
            or_(
                Chat.init_id == user.id,
                Chat.other_id == user.id
            )
        ).all()

        result = [x.other if x.init_id == user.id else x.init for x in contacts]
        return result

    def get_message_history(self, user: User) -> List[Message]:

        messages: List[MessageHistory] = self._db.query(MessageHistory).filter(
                MessageHistory.recipient_id == user.id
        ).filter(MessageHistory.sent.is_(False)).all()

        for mess in messages:
            mess.sent = True
            self._db.add(mess)
        self._db.commit()

        result = [Message(
            to=x.recipient.login,
            from_=x.sender.login,
            message=x.content,
            date=x.date.strftime(settings.DATE_FORMAT)
        ) for x in messages]

        return result

    def create_message(self, data: Message, sent: bool):
        sender = self.get_user(data.from_)
        if not sender:
            raise NotExist(f"Пользователь {data.from_} не существует")

        recipient = self.get_user(data.to)
        if not recipient:
            raise NotExist(f"Пользователь {data.from_} не существует")

        message = MessageHistory(
            date=datetime.datetime.strptime(data.date, settings.DATE_FORMAT),
            content=data.message,
            sender=sender,
            recipient=recipient,
            sent=sent
        )
        self._db.add(message)
        self._db.commit()

    def create_chat(self, user: User, other: User) -> int:

        exist = self._db.query(Chat).filter(
            or_(
                and_(Chat.init_id == user.id, Chat.other_id == other.id),
                and_(Chat.init_id == other.id, Chat.other_id == user.id)
            )
        ).one_or_none()

        if exist:
            raise AlreadyExist("Чат уже существует")

        init = self.get_user(user.login)
        other = self.get_user(other.login)

        obj = Chat(
            init=init,
            other=other
        )
        self._db.add(obj)
        self._db.commit()
        return obj.id

    def delete_chat(self, user: User, other: User):

        chat = self._db.query(Chat).filter(or_(
            and_(
                Chat.init_id == user.id,
                Chat.other_id == other.id
            ),
            and_(
                Chat.init_id == other.id,
                Chat.other_id == user.id
            )
        )).one_or_none()

        if not chat:
            raise NotExist('Chat not exist')

        self._db.delete(chat)
        self._db.commit()
