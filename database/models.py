import datetime

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, orm, Boolean
from werkzeug.security import generate_password_hash, check_password_hash

from database.session import SqlAlchemyBase
from core.utilities import get_created_time, Pagination


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

    def get_created_time(self) -> str:
        """Получить дату и время создания пользователя в удобном виде"""
        return get_created_time(self.created_time)


class Category(SqlAlchemyBase):
    """Модель категории"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, unique=True)

    topics = orm.relation("Topic", back_populates="category")

    def get_topics_pagination(self, step: int = 10) -> Pagination:
        """
        Получить разделить список тем на страницы

        :arg step: количество тем на странице
        """
        return Pagination(sorted(self.topics, key=lambda t: (t.is_pinned, t.created_time), reverse=True), step)


class Topic(SqlAlchemyBase):
    """Модель темы"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String)
    text = Column(String)
    is_pinned = Column(Boolean, default=False)
    created_time = Column(DateTime, default=datetime.datetime.now)

    author = orm.relation("User")
    category = orm.relation("Category")
    comments = orm.relation("Comment", back_populates="topic")

    def get_created_time(self) -> str:
        """Получить дату и время создания темы в удобном виде"""
        return get_created_time(self.created_time)

    def get_comments_pagination(self, step: int = 10) -> Pagination:
        """
        Получить разделить список комментариев на страницы

        :arg step: количество комментариев на странице
        """
        return Pagination(sorted(self.comments, key=lambda c: c.created_time), step)


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

    def get_created_time(self) -> str:
        """Получить дату и время создания комментария в удобном виде"""
        return get_created_time(self.created_time)
