import datetime

from sqlalchemy import Column, Integer, String, DateTime

from .session import SqlAlchemyBase


# Модели базы данных
class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_time = Column(DateTime, default=datetime.datetime.now)
