import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

SqlAlchemyBase = declarative_base()
__factory = None


def global_init(database_url: str):
    """Инициализация подключения к базе данных"""
    global __factory

    if __factory:
        return

    engine = sqlalchemy.create_engine(database_url, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """Создать сессию с базой данных"""
    global __factory
    return __factory()
