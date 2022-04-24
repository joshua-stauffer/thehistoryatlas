"""SQLAlchemy database schema for the Accounts service.

October 16th 2021
"""

from ctypes.wintypes import BOOL
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT, BOOLEAN
from app.types import UserDetails
from app.utils import update_last_login

Base = declarative_base()

# the following fields cannot be updated by users
PROTECTED_FIELDS = {"type", "last_login", "disabled", "id", "confirmed"}


class User(Base):
    """Model representing Users and their data"""

    __tablename__ = "users"
    id = Column(VARCHAR, primary_key=True)
    email = Column(VARCHAR)
    f_name = Column(VARCHAR)
    l_name = Column(VARCHAR)
    username = Column(VARCHAR, unique=True)
    password = Column(VARCHAR)
    type = Column(VARCHAR, default="contrib")  # "admin" or "contrib"
    last_login = Column(
        VARCHAR, onupdate=update_last_login, default=update_last_login
    )
    deactivated = Column(BOOLEAN, default=False)
    confirmed = Column(BOOLEAN, default=False)

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
            "last_login": self.last_login,
        }
