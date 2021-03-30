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

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Topic(SqlAlchemyBase):
    """Модель темы"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    created_time = Column(DateTime, default=datetime.datetime.now)

    author = orm.relation("User")
    comments = orm.relation("Comment", back_populates="topic")


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
