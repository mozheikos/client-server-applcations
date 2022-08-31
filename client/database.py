import datetime
from typing import List

from sqlalchemy.engine import Engine

from client.models import create_tables, Contact, History
from common.config import settings
from common.exceptions import AlreadyExist

from db.core import Database
from templates.templates import User, Request


class ClientDatabase(Database):

    def __init__(self, login: str):
        super(ClientDatabase, self).__init__(login)

    @staticmethod
    def _create_tables(engine: Engine):
        return create_tables(engine)

    def save_contact(self, user: User):
        exist = self._db.query(Contact).filter(Contact.id == user.id).one_or_none()
        if exist:
            raise AlreadyExist

        contact = Contact(
            id=user.id,
            login=user.login,
            verbose_name=user.verbose_name
        )
        self._db.add(contact)
        self._db.commit()

    def save_contacts(self, users: List[User]):
        for user in users:
            try:
                self.save_contact(user)
            except AlreadyExist:
                continue

    def get_contact(self, login: str) -> Contact:
        contact = self._db.query(Contact).filter(Contact.login == login).one_or_none()
        if contact:
            return contact

    def get_contacts(self) -> List[Contact]:

        contacts = self._db.query(Contact).all()
        return [x for x in contacts]

    def get_messages(self) -> List[History]:
        messages = self._db.query(History).all()
        return messages

    def save_message(self, request: Request, kind: str):

        if kind == 'outbox':
            contact = self.get_contact(request.data.to)
        else:
            contact = self.get_contact(request.data.from_)

        if contact:

            msg = History(
                kind=kind,
                date=datetime.datetime.strptime(request.data.date, settings.DATE_FORMAT),
                text=request.data.message,
                contact=contact
            )
            self._db.add(msg)
            self._db.commit()

    def save_messages(self, request: Request):

        to_db = []
        for message in request.data:
            contact = self.get_contact(message.from_)
            to_db.append(
                History(
                    kind='inbox',
                    date=datetime.datetime.strptime(message.date, settings.DATE_FORMAT),
                    text=message.message,
                    contact=contact
                )
            )

        self._db.add_all(to_db)
        self._db.commit()
