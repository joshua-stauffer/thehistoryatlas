from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import VARCHAR, BOOLEAN

from the_history_atlas.apps.accounts.types import UserDetailsDict
from the_history_atlas.apps.accounts.utils import update_last_login

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
    last_login = Column(VARCHAR, onupdate=update_last_login, default=update_last_login)
    deactivated = Column(BOOLEAN, default=False)
    confirmed = Column(BOOLEAN, default=False)

    @property
    def is_admin(self):
        return self.type == "admin"

    def to_dict(self) -> UserDetailsDict:
        """returns all queryable fields on the User object"""
        return {
            "f_name": self.f_name,
            "l_name": self.l_name,
            "username": self.username,
            "email": self.email,
            "last_login": self.last_login,
        }
