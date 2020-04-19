import datetime

import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase

class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    friends = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    avatar = sqlalchemy.Column(sqlalchemy.String,
                               default='/static/img/backgrounds/default.png')
    liked_news = sqlalchemy.Column(sqlalchemy.VARCHAR, nullable=True)
    liked_photos = sqlalchemy.Column(sqlalchemy.VARCHAR, nullable=True)
    background = sqlalchemy.Column(sqlalchemy.String, default='/static/img/backgrounds/default.png')
    theme = sqlalchemy.Column(sqlalchemy.Boolean, default=1)
    albums = sqlalchemy.Column(sqlalchemy.VARCHAR)


def __repr__(self):
    return f"<User> {self.id} {self.name} {self.email}"

def set_password(self, password):
    self.hashed_password = generate_password_hash(password)


def check_password(self, password):
    return check_password_hash(self.hashed_password, password)
