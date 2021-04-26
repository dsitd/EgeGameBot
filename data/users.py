import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    id_player = sqlalchemy.Column(sqlalchemy.Integer, index=True)
    result_game = sqlalchemy.Column(sqlalchemy.Boolean)
    game_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)