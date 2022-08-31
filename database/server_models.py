import sqlalchemy.exc
from sqlalchemy import Column, ForeignKey, Boolean
from sqlalchemy.dialects.sqlite import INTEGER, VARCHAR, DATETIME, BOOLEAN
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    id = Column(INTEGER, primary_key=True)
    login = Column(VARCHAR, unique=True, nullable=False)
    password = Column(VARCHAR, nullable=False)
    verbose_name = Column(VARCHAR, nullable=False)
    created_at = Column(DATETIME)

    connect_history = relationship(
        'ClientHistory',
        back_populates='client',
        uselist=True
    )


class ClientHistory(Base):
    __tablename__ = 'clients_history'

    id = Column(INTEGER, primary_key=True)
    client_id = Column(INTEGER, ForeignKey('clients.id', ondelete='CASCADE', onupdate='CASCADE'))
    date = Column(DATETIME, nullable=False)
    address = Column(VARCHAR, nullable=False)

    client = relationship(
        Client,
        back_populates='connect_history',
        uselist=False
    )


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(INTEGER, primary_key=True)
    init_id = Column(INTEGER, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    other_id = Column(INTEGER, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)

    init = relationship(
        Client,
        foreign_keys=[init_id],
        uselist=False
    )

    other = relationship(
        Client,
        foreign_keys=[other_id],
        uselist=False
    )


class MessageHistory(Base):
    __tablename__ = 'messages'

    id = Column(INTEGER, primary_key=True)
    sender_id = Column(INTEGER, ForeignKey('clients.id', onupdate='CASCADE', ondelete='SET NULL'))
    recipient_id = Column(INTEGER, ForeignKey('clients.id', onupdate='CASCADE', ondelete='SET NULL'))
    date = Column(DATETIME, nullable=False)
    content = Column(VARCHAR, nullable=False)
    sent = Column(BOOLEAN)

    sender = relationship(
        Client,
        foreign_keys=[sender_id],
        uselist=False
    )

    recipient = relationship(
        Client,
        foreign_keys=[recipient_id],
        uselist=False
    )


def create_tables(engine: Engine):
    result = True
    try:
        metadata = Base.metadata
        metadata.create_all(bind=engine, checkfirst=True)
    except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.InterfaceError):
        result = False
    finally:
        return result
