"""Component responsible for fielding queries on the Accounts service.

Sunday, October 17th 2021
"""

import logging
from app.errors import UnknownQueryError
from app.errors import MissingUserError
from app.errors import AuthenticationError
from app.errors import DeactivatedUserError
from app.errors import MissingFieldsError
from app.errors import UnauthorizedUserError
from app.schema import User

log = logging.getLogger(__name__)


class QueryHandler:

    def __init__(self, database_instance):
        self._db = database_instance
        self._query_handlers = self._map_query_handlers()

    def handle_query(self, query) -> dict:
        """Process incoming queries and return results"""
        log.info(f'Handling a query: {query}')
        query_type = query.get('type')
        handler = self._query_handlers.get(query_type)
        if not handler:
            raise UnknownQueryError(query_type)
        try:
            res = handler(query)
        except KeyError:
            # globally catch all missing fields
            raise MissingFieldsError
        return res

    def _map_query_handlers(self):
        """A dict of known query types and the methods which process them"""
        return {
            "LOGIN": self._handle_login,
            "ADD_USER": self._handle_add_user,
            "GET_USER": self._handle_get_user,
            "UPDATE_USER": self._handle_update_user,
            "IS_USERNAME_UNIQUE": self._handle_is_username_unique,
            "DEACTIVATE_ACCOUNT": self._handle_deactivate_account,
            "CONFIRM_ACCOUNT": self._handle_confirm_account,
        }

    def _handle_login(self, query):
        """Attempt to verify user credentials and return token if successful"""

        username = query['payload']['username']
        password = query['payload']['password']
        # raises error if unsuccessful
        try:
            token = self._db.login(username, password)
            return {
                'type': 'LOGIN',
                'payload': {
                    'success': True,
                    'token': token
                }
            }
        except MissingUserError or DeactivatedUserError or AuthenticationError:
            return {
                'type': 'LOGIN',
                'payload': {
                    'success': False,
                }
            }

    def _handle_add_user(self, query):
        """Add a user. Requires admin credentials"""
        token=query["payload"]["token"]
        user_details = query["payload"]["user_data"]
        token, user_details = self._db.add_user(
            token, user_details
        )
        return {
            'type': 'ADD_USER',
            'payload': {
                'token': token,
                'user_details': user_details
            }
        }

    def _handle_update_user(self, query):
        """Updates a user's information"""
        token = query["payload"]["token"]
        user_details = query["payload"]["user_data"]
        token, user_details = self._db.update_user(
            token=token,
            user_data=user_details
        )
        return {
            'type': 'UPDATE_USER',
            'payload': {
                'token': token,
                'user_details': user_details
            }
        }

    def _handle_get_user(self, query):
        """Fetches a user's information"""
        token = query["payload"]["token"]
        token, user_details = self._db.get_user(token=token)
        return {
            'type': 'GET_USER',
            'payload': {
                'token': token,
                'user_details': user_details
            }
        }

    def _handle_is_username_unique(self, query):
        """Test if a given username is already in use."""

        username = query['payload']['username']
        res = self._db.check_if_username_is_unique(username)
        return {
            'type': 'IS_USERNAME_UNIQUE',
            'payload': {
                'is_unique': res,
                'username': username
            }
        }

    def _handle_deactivate_account(self, query):
        """Deactivate a user's account. Requires admin credentials"""
        token = query['payload']['token']
        username = query['payload']['username']
        token, user_details = self._db.deactivate_account(token, username)
        return {
            'type': 'DEACTIVATE_ACCOUNT',
            'payload': {
                'token': token,
                'user_details': user_details
            }
        }

    def _handle_confirm_account(self, query):
        """Path for user to verify their email address"""
        token = query['payload']['token']
        token, user_details = self._db.confirm_account(token)
        return {
            'type': 'CONFIRM_ACCOUNT',
            'payload': {
                'token': token,
                'user_details': user_details
            }
        }
