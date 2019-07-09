from .resources import database, metadata

import orm


class User(orm.Model):
    __tablename__ = "users"
    __database__ = database
    __metadata__ = metadata

    id = orm.Integer(primary_key=True)
    username = orm.String(max_length=100)
    password = orm.String(max_length=200)
    date_joined = orm.DateTime()
    last_login = orm.DateTime()
    is_admin = orm.Boolean(default=False)
