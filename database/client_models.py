import sqlalchemy.exc
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import INTEGER, VARCHAR, DATETIME
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(INTEGER, primary_key=True)
    login = Column(VARCHAR, unique=True, nullable=False)
    verbose_name = Column(VARCHAR, nullable=False)

    history = relationship(
        'History',
        back_populates='contact',
        uselist=True
    )


class History(Base):
    __tablename__ = 'history'

    id = Column(INTEGER, primary_key=True)
    contact_id = Column(INTEGER, ForeignKey('contacts.id', ondelete='CASCADE', onupdate='CASCADE'))
    kind = Column(VARCHAR, nullable=False)
    date = Column(DATETIME, nullable=True)
    text = Column(VARCHAR)

    contact = relationship(
        Contact,
        back_populates='history',
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
