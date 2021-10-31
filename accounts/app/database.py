"""
SQLAlchemy integration for the History Atlas Accounts service.
Allows creation and updating users
"""

import asyncio
import logging
import json
from uuid import uuid4
from typing import Dict
from typing import Tuple
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
from app.errors import UnconfirmedUserError
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
        
    def add_user(self, token: Token, user_data: Dict) -> UserDetails:
        """Adds a user to the database"""


        user_id, token = validate_token(token)
        with Session(self._engine, future=True) as session:
            self._require_admin_user(
                user_id=user_id,
                session=session,
            )

            for field in user_data.keys():
                if field in PROTECTED_FIELDS:
                    raise UnauthorizedUserError

            # don't mutate original dict
            user_data = {
                **user_data,
                'id': str(uuid4()),
                'type': 'contrib',
                'confirmed': False,
                'deactivated': False
            }

            # handle password
            password = user_data["password"]
            user_data["password"] = encrypt(password)
            # create user object
            new_user = User(**user_data)
        
            session.add(new_user)
            session.commit()

            # TODO: when email service is enabled, add call here to send a token to
            # the provided email address.

            return token, new_user.to_dict()

    def update_user(self, token, user_data) -> Tuple[Token, UserDetails]:
        """Update a user's data"""

        user_id, token = validate_token(token)
        
        with Session(self._engine, future=True) as session:
            user = self._get_user_by_id(user_id, session)
            for key, val in user_data.items():
                if key in PROTECTED_FIELDS:
                    if not user.is_admin:
                        raise UnauthorizedUserError
                setattr(user, key, val)
            session.add(user)
            session.commit()
            return token, user.to_dict()

    def get_user(self, token) -> Tuple[Token, UserDetails]:
        """Obtain user details"""

        user_id, token = validate_token(token)
        with Session(self._engine, future=True) as session:
            user = self._get_user_by_id(user_id=user_id, session=session)
            return token, user.to_dict()

    def login(self, username, password) -> Token:
        """Exchange login credentials for a token"""

        with Session(self._engine, future=True) as session:
            user = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            if not user:
                raise MissingUserError
            if user.deactivated:
                raise DeactivatedUserError
            if not check_password(password, user.password):
                raise AuthenticationError
            if not user.confirmed:
                raise UnconfirmedUserError
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

    def deactivate_account(self, token, user_id) -> Tuple[Token, UserDetails]:
        admin_user_id, token = validate_token(token)
        with Session(self._engine, future=True) as session:
            self._require_admin_user(user_id=admin_user_id, session=session)
            user = self._get_user_by_id(user_id=user_id, session=session)
            user.deactivated = True
            session.add(user)
            session.commit()
            return token, user.to_dict()

    def confirm_account(self, token) -> Tuple[Token, UserDetails]:
        user_id, token = validate_token(token, force_refresh=True)
        with Session(self._engine, future=True) as session:
            user = self._get_user_by_id(user_id, session)
            user.confirmed = True
            session.add(user)
            session.commit()
            return token, user.to_dict()

    @staticmethod
    def _get_user_by_id(user_id, session):
        """internal helper method to retrieve a user object by id.
        Must be called within context of active session."""

        user = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        if not user:
            raise MissingUserError
        if user.deactivated:
            raise DeactivatedUserError
        return user

    def _require_admin_user(self, user_id, session) -> bool:
        user = self._get_user_by_id(user_id, session)
        if not user.is_admin:
            raise UnauthorizedUserError
        return True
