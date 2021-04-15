import datetime

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, orm
from werkzeug.security import generate_password_hash, check_password_hash

from .session import SqlAlchemyBase


# Модели базы данных
class User(SqlAlchemyBase, UserMixin):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_time = Column(DateTime, default=datetime.datetime.now)

    topics = orm.relation("Topic", back_populates="author")
    comments = orm.relation("Comment", back_populates="author")

    def set_password(self, password: str):
        """Поставить пароль"""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Проверить пароль по хешу"""
        return check_password_hash(self.hashed_password, password)

    def get_created_time(self, time: bool = False) -> str:
        """
        Получить дату и время создания пользователя в удобном виде

        :arg time: вернуть дату с временем
        """
        return self.created_time.strftime(f"%d.%m.%Y{' %H:%M:%S' if time else ''}")


class Category(SqlAlchemyBase):
    """Модель категории"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, unique=True)

    topics = orm.relation("Topic", back_populates="category")


class Topic(SqlAlchemyBase):
    """Модель темы"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String)
    text = Column(String)
    created_time = Column(DateTime, default=datetime.datetime.now)

    author = orm.relation("User")
    category = orm.relation("Category")
    comments = orm.relation("Comment", back_populates="topic")

    def get_created_time(self, time=False) -> str:
        """
        Получить дату и время создания темы в удобном виде

        :arg time: вернуть дату с временем
        """
        return self.created_time.strftime(f"%d.%m.%Y{' %H:%M:%S' if time else ''}")


class Comment(SqlAlchemyBase):
    """Модель комментария в теме"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    text = Column(String, nullable=False)
    created_time = Column(DateTime, default=datetime.datetime.now)

    author = orm.relation("User")
    topic = orm.relation("Topic")

    def get_created_time(self, time=False) -> str:
        """
        Получить дату и время создания комментария в удобном виде

        :arg time: вернуть дату с временем
        """
        return self.created_time.strftime(f"%d.%m.%Y{' %H:%M:%S' if time else ''}")
