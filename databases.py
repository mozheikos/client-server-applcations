import datetime
from typing import List, Optional

from sqlalchemy import or_, and_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from common.config import settings
from common.utils import get_hashed_password
from database.client_models import Contact, History
from database.core import DatabaseFactory
from database.server_models import MessageHistory, Client, ClientHistory, create_tables, Chat
from database.client_models import create_tables as create_client_tables
from exceptions import NotExist, AlreadyExist
from templates.templates import Message, User, Request


class Database:
    def __init__(self):
        self.__create_tables = create_tables if self.__class__.__name__ == 'ServerDatabase' else create_client_tables
        self._db = self._connect()

    def _get_database(self) -> Engine:
        factory = DatabaseFactory(self.__class__.__name__)
        return factory.get_engine()

    def _connect(self) -> Session:
        engine = self._get_database()
        db_init = self.__create_tables(engine)
        if db_init:
            return Session(bind=engine)
        raise NotExist("Database creation error")
        
    def __del__(self):
        self._db.close()


class ServerDatabase(Database):

    def __init__(self):
        super(ServerDatabase, self).__init__()

    def get_user(self, username: str) -> Optional[Client]:
        user: Client = self._db.query(Client).filter(Client.login == username).one_or_none()
        return user

    def search(self, value: str) -> Client:
        user = self._db.query(Client).filter(Client.login == value).one_or_none()
        if not user:
            raise NotExist
        return user

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
            or_(
                MessageHistory.sender_id == user.id,
                MessageHistory.recipient_id == user.id
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
            raise NotExist(f"Пользователь {data.from_} не существует")

        recipient = self.get_user(data.to)
        if not recipient:
            raise NotExist(f"Пользователь {data.from_} не существует")

        message = MessageHistory(
            date=datetime.datetime.strptime(data.date, settings.DATE_FORMAT),
            content=data.message,
            sender=sender,
            recipient=recipient
        )
        self._db.add(message)
        self._db.commit()

    def create_chat(self, user: User, other: User) -> int:

        exist = self._db.query(Chat).filter(
            or_(
                and_(Chat.init_id == user.id, Chat.other.id == other.id),
                and_(Chat.init.id == other.id, Chat.other_id == user.id)
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


class ClientDatabase(Database):

    def __init__(self):
        super(ClientDatabase, self).__init__()

    def save_contact(self, user: User, owner: str):
        exist = self._db.query(Contact).filter(Contact.id == user.id).one_or_none()
        if exist:
            raise AlreadyExist

        contact = Contact(
            id=user.id,
            owner=owner,
            login=user.login,
            verbose_name=user.verbose_name
        )
        self._db.add(contact)
        self._db.commit()

    def save_contacts(self, users: List[User], owner: str):
        for user in users:
            try:
                self.save_contact(user, owner)
            except AlreadyExist:
                continue

    def get_contact(self, login: str, owner: str) -> Contact:
        contact = self._db.query(Contact).filter(Contact.login == login).filter(Contact.owner == owner).one_or_none()
        if contact:
            return contact

    def get_contacts(self, owner: str) -> List[Contact]:

        contacts = self._db.query(Contact).filter(Contact.owner == owner).all()
        return [x for x in contacts]

    def get_messages(self, owner: str) -> List[History]:
        messages = self._db.query(History).filter(
            History.owner == owner
        ).all()
        return messages

    def save_message(self, request: Request, kind: str, owner: str):

        if kind == 'outbox':
            contact = self.get_contact(request.data.to, owner)
        else:
            contact = self.get_contact(request.data.from_, owner)

        msg = History(
            kind=kind,
            date=datetime.datetime.strptime(request.time, settings.DATE_FORMAT),
            text=request.data.message,
            owner=owner,
            contact=contact
        )
        self._db.add(msg)
        self._db.commit()
