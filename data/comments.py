import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Comment(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'comments'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    text = sqlalchemy.Column(sqlalchemy.String)
    news_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("news.id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    news = orm.relation('News')
    user = orm.relation('User')
