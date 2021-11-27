"""
SQLAlchemy integration for the History Atlas Accounts service.
Allows creation and updating users
"""

import asyncio
import logging
import json
from uuid import uuid4
from typing import (
    Dict,
    Optional,
    Tuple,
)
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
from app.errors import DuplicateUsernameError
from app.encryption import get_token
from app.encryption import encrypt
from app.encryption import check_password
from app.encryption import validate_token
from app.types import Token
from app.types import UserDetails


log = logging.getLogger(__name__)


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)
        # dev only, create a default admin user
        self._ensure_admin()

    def add_user(self, token: Token, user_details: Dict) -> UserDetails:
        """Adds a user to the database"""

        user_id, token = validate_token(token)
        if not self.check_if_username_is_unique(user_details["username"]):
            raise DuplicateUsernameError
        with Session(self._engine, future=True) as session:
            self._require_admin_user(
                user_id=user_id,
                session=session,
            )

            for field in user_details.keys():
                if field in PROTECTED_FIELDS:
                    raise UnauthorizedUserError

            # don't mutate original dict
            user_details = {
                **user_details,
                "id": str(uuid4()),
                "type": "contrib",
                "confirmed": False,
                "deactivated": False,
            }

            # handle password
            password = user_details["password"]
            user_details["password"] = encrypt(password)
            # create user object
            new_user = User(**user_details)

            session.add(new_user)
            session.commit()

            # TODO: when email service is enabled, add call here to send a token to
            # the provided email address.
            new_user_token = get_token(new_user.id)
            log.info(f"New User Token is: {new_user_token}")

            return token, new_user.to_dict()

    def update_user(
        self, token: str, user_details: dict, credentials: Optional[dict[str, str]]
    ) -> Tuple[Token, UserDetails]:
        """Update a user's data"""

        user_id, token = validate_token(token)

        if "password" in user_details or "username" in user_details:
            # Must login again to change access credentials
            token = self.login(  # will raise an error if login fails
                username=credentials["username"], password=credentials["password"]
            )
        if "password" in user_details:  # encrypt new password
            password = user_details["password"]
            user_details["password"] = encrypt(password)

        with Session(self._engine, future=True) as session:
            user = self._get_user_by_id(user_id, session)
            for key, val in user_details.items():
                if key in PROTECTED_FIELDS:
                    if not user.is_admin:
                        raise UnauthorizedUserError
                setattr(user, key, val)
            session.add(user)
            session.commit()
            return str(token), user.to_dict()

    def get_user(self, token) -> Tuple[Token, UserDetails]:
        """Obtain user details"""

        user_id, token = validate_token(token)
        with Session(self._engine, future=True) as session:
            user = self._get_user_by_id(user_id=user_id, session=session)
            return str(token), user.to_dict()

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
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            if user:
                return False
            return True

    def deactivate_account(self, token, username) -> Tuple[Token, UserDetails]:
        admin_user_id, token = validate_token(token)
        with Session(self._engine, future=True) as session:
            self._require_admin_user(user_id=admin_user_id, session=session)
            user = self._get_user_by_name(username=username, session=session)
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
        """
        Internal util to retrieve a user object by id.
        Must be called within context of active session.
        """

        user = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        if not user:
            raise MissingUserError
        if user.deactivated:
            raise DeactivatedUserError
        return user

    @staticmethod
    def _get_user_by_name(username, session):
        """
        Internal util to retrieve a user object by username.
        Must be called within context of active session.
        """

        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if not user:
            raise MissingUserError
        if user.deactivated:
            raise DeactivatedUserError
        return user

    def _require_admin_user(self, user_id, session) -> bool:
        """
        Internal util to check if a user is admin.
        Raises UnauthorizedUserError if user is not.
        Must be called within context of active session.
        """
        user = self._get_user_by_id(user_id, session)
        if not user.is_admin:
            raise UnauthorizedUserError
        return True

    def _ensure_admin(self):
        """
        For development use only. Creates a default admin user
        if one does not yet exist.
        """
        with Session(self._engine, future=True) as session:
            accounts = session.query(User).all()
            if len(accounts):
                log.info("Found an existing account.")
                return
            log.info("Creating a default admin account.")
            # cur_user = session.query(User).filter(User.username == 'admin').one()
            # session.delete(cur_user)
            # session.commit()
            user = User(
                id=str(uuid4()),
                username="admin",
                password=encrypt("admin"),
                f_name="tha",
                l_name="admin",
                email="test@thehistoryatlas.org",
                type="admin",
                confirmed=True,
                deactivated=False,
            )
            session.add(user)
            session.commit()
