import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Photo(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'albums'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    photos = sqlalchemy.Column(sqlalchemy.VARCHAR)
    about = sqlalchemy.Column(sqlalchemy.VARCHAR)
    cover = sqlalchemy.Column(sqlalchemy.String)