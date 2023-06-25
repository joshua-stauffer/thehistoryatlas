import logging

from the_history_atlas.apps.accounts.errors import (
    MissingUserError,
    DeactivatedUserError,
    AuthenticationError,
)
from the_history_atlas.apps.config import Config

from the_history_atlas.apps.accounts.database import Database


logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class Accounts:
    """Primary class for application. Primarily coordinates AMQP broker with
    database connection."""

    def __init__(self, config: Config):
        self._config = config
        self._db = Database(self._config)

    def login(self, query):
        """Attempt to verify user credentials and return token if successful"""

        username = query["payload"]["username"]
        password = query["payload"]["password"]
        # raises error if unsuccessful
        try:
            token = self._db.login(username, password)
            return {"type": "LOGIN", "payload": {"success": True, "token": token}}
        except MissingUserError or DeactivatedUserError or AuthenticationError:
            return {
                "type": "LOGIN",
                "payload": {
                    "success": False,
                },
            }

    def add_user(self, query):
        """Add a user. Requires admin credentials"""
        token = query["payload"]["token"]
        user_details = query["payload"]["user_details"]
        token, user_details = self._db.add_user(token=token, user_details=user_details)
        return {
            "type": "ADD_USER",
            "payload": {"token": token, "user_details": user_details},
        }

    def update_user(self, query):
        """Updates a user's information"""
        token = query["payload"]["token"]
        user_details = query["payload"]["user_details"]
        credentials = query["payload"].get("credentials", None)
        token, user_details = self._db.update_user(
            token=token, user_details=user_details, credentials=credentials
        )
        return {
            "type": "UPDATE_USER",
            "payload": {"token": token, "user_details": user_details},
        }

    def get_user(self, query):
        """Fetches a user's information"""
        token = query["payload"]["token"]
        token, user_details = self._db.get_user(token=token)
        return {
            "type": "GET_USER_RESPONSE",
            "payload": {"token": token, "user_details": user_details},
        }

    def is_username_unique(self, query):
        """Test if a given username is already in use."""

        username = query["payload"]["username"]
        res = self._db.check_if_username_is_unique(username)
        return {
            "type": "IS_USERNAME_UNIQUE",
            "payload": {"is_unique": res, "username": username},
        }

    def deactivate_account(self, query):
        """Deactivate a user's account. Requires admin credentials"""
        token = query["payload"]["token"]
        username = query["payload"]["username"]
        token, user_details = self._db.deactivate_account(token, username)
        return {
            "type": "DEACTIVATE_ACCOUNT",
            "payload": {"token": token, "user_details": user_details},
        }

    def confirm_account(self, query):
        """Path for user to verify their email address"""
        token = query["payload"]["token"]
        token, user_details = self._db.confirm_account(token)
        return {
            "type": "CONFIRM_ACCOUNT",
            "payload": {"token": token, "user_details": user_details},
        }
