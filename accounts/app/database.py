"""
SQLAlchemy integration for the History Atlas Accounts service.
Allows creation and updating users
"""

import asyncio
import logging
import json
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schema import PROTECTED_FIELDS
from app.schema import User
from app.schema import Base
from app.errors import AuthenticationError
from app.errors import MissingFieldsError
from app.errors import MissingUserError
from app.errors import DeactivatedUserError
from app.errors import UnauthorizedUserError
from app.encryption import get_token
from app.encryption import encrypt
from app.encryption import check_password
from app.encryption import validate_token
from app.types import Token
from app.types import UserDetails


log = logging.getLogger(__name__)

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)
        
    def add_user(self, user_data: Dict) -> None:
        """Adds a user to the database"""

        # don't mutate original dict
        user_data = {**user_data}
        try:
            # handle password
            password = user_data["password"]
            user_data["password"] = encrypt(password)
            # create user object
            new_user = User(**user_data)
        except KeyError:
            raise MissingFieldsError
        
        with Session(self._engine, future=True) as session:
            session.add(new_user)
            session.commit()

    def update_user(self, token, user_dict) -> UserDetails:
        """Update a user's data"""

        user_id = get_user_from_token(token)
        
        with Session(self._engine, future=True) as session:
            user = session.execute(
                select(User).where(User.id==user_id)
            ).scalar_one_or_none()
            if not user:
                raise MissingUserError
            for key, val in user_dict.items():
                if not user.is_admin and key in PROTECTED_FIELDS:
                    raise UnauthorizedUserError
                setattr(user, key, val)
            session.add(user)
            session.commit()

    def get_user(self, token) -> UserDetails:
        """Obtain user details"""

        username = validate_token(token)
        with Session(self._engine, future=True) as session:
            user = session.execute(
                select(User).where(User.username==username)
            ).scalar_one_or_none()
            if not user:
                raise MissingUserError
            if user.deactivated:
                raise DeactivatedUserError
            


    def login(self, username, password) -> Token:
        """Exchange login credentials for a token"""

        with Session(self._engine, future=True) as session:
            user = session.execute(
                select(User).where(User.username==username)
            ).scalar_one_or_none()
            if not user:
                raise MissingUserError
            if user.deactivated:
                raise DeactivatedUserError
            if not check_password(password, user.password):
                raise AuthenticationError
            token = get_token(user.id)
        return token

    def check_if_username_is_unique(self, username) -> bool:
        """Returns True if a username is unique else False."""

        with Session(self._engine, future=True) as session:
            user = session.execute(
                select(User).where(User.username==username)
            ).scalar_one_or_none()
            if user:
                return False
            return True
