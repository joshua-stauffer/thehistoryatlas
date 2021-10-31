"""SQLAlchemy database schema for the Accounts service.

October 16th 2021
"""

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
from sqlalchemy.sql.sqltypes import Boolean
from app.types import UserDetails
from app.utils import update_last_login

Base = declarative_base()

# the following fields cannot be updated by users
PROTECTED_FIELDS = {"type", "last_login", "disabled", "id"}


class User(Base):
    """Model representing Users and their data"""

    __tablename__ = 'users'
    id = Column(String(64), primary_key=True)
    email = Column(String(128))
    f_name = Column(String(64))
    l_name = Column(String(64))
    username = Column(String(64), unique=True)
    password = Column(String(128))
    type = Column(String(8), default='contrib')  # "admin" or "contrib"
    last_login = Column(String(32), onupdate=update_last_login)
    deactivated = Column(Boolean, default=False)
    confirmed = Column(Boolean, default=False)

    @property
    def is_admin(self):
        return self.type == "admin"

    def to_dict(self) -> UserDetails:
        """returns all queriable fields on the User object"""
        return {
                "f_name": self.f_name,
                "l_name": self.l_name,
                "username": self.username,
                "email": self.email,
                "last_login": self.last_login
            }
