from .db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm


class Good(SqlAlchemyBase):
    __tablename__ = 'goods'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Float)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    photo = sqlalchemy.Column(sqlalchemy.String)

    user = orm.relation('User')
