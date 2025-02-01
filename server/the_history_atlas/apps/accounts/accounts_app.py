import logging
from dataclasses import asdict
from typing import Dict

from sqlalchemy.engine import Engine

from the_history_atlas.apps.accounts.errors import (
    MissingUserError,
    DeactivatedUserError,
    AuthenticationError,
    UnconfirmedUserError,
)
from the_history_atlas.apps.config import Config

from the_history_atlas.apps.accounts.repository import Repository
from the_history_atlas.apps.domain.models.accounts import (
    LoginResponse,
    Credentials,
    UserDetails,
)
from the_history_atlas.apps.domain.models.accounts.add_user import (
    AddUserPayload,
    AddUserResponsePayload,
)
from the_history_atlas.apps.domain.models.accounts.confirm_account import (
    ConfirmAccountResponsePayload,
)
from the_history_atlas.apps.domain.models.accounts.deactivate_account import (
    DeactivateAccountResponsePayload,
    DeactivateAccountPayload,
)
from the_history_atlas.apps.domain.models.accounts.get_user import (
    GetUserResponsePayload,
    GetUserPayload,
)
from the_history_atlas.apps.domain.models.accounts.is_username_unique import (
    IsUsernameUniqueResponsePayload,
    IsUsernameUniquePayload,
)
from the_history_atlas.apps.domain.models.accounts.update_user import (
    UpdateUserResponsePayload,
    UpdateUserPayload,
)

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class AccountsApp:
    """Business logic for managing Accounts."""

    def __init__(self, config: Config, database_client: Engine):
        self._config = config
        self._repository = Repository(engine=database_client)

    def login(self, data: Credentials) -> LoginResponse:
        """Attempt to verify user credentials and return token if successful"""
        try:
            token = self._repository.login(data.username, data.password)
            success = True
        except (
            MissingUserError,
            DeactivatedUserError,
            AuthenticationError,
            UnconfirmedUserError,
        ):
            success = False
            token = None
        return LoginResponse(success=success, token=token)

    def add_user(self, data: AddUserPayload) -> AddUserResponsePayload:
        """Add a user. Requires admin credentials"""
        token, user_details = self._repository.add_user(
            token=data.token, user_details=data.user_details
        )
        return AddUserResponsePayload(
            token=token, user_details=UserDetails(**user_details)
        )

    def update_user(self, data: UpdateUserPayload) -> UpdateUserResponsePayload:
        """Updates a user's information"""

        token, user_details = self._repository.update_user(
            token=data.token,
            user_details=data.user_details,
            credentials=data.credentials.dict(),  # todo: update db to use object
        )
        return UpdateUserResponsePayload(
            token=token, user_details=UserDetails(**user_details)
        )

    def get_user(self, data: GetUserPayload) -> GetUserResponsePayload:
        """Fetches a user's information"""
        token, user_details = self._repository.get_user(token=data.token)
        return GetUserResponsePayload(
            token=token, user_details=UserDetails(**user_details)
        )

    def is_username_unique(
        self, data: IsUsernameUniquePayload
    ) -> IsUsernameUniqueResponsePayload:
        """Test if a given username is already in use."""

        res = self._repository.check_if_username_is_unique(data.username)
        return IsUsernameUniqueResponsePayload(is_unique=res, username=data.username)

    def deactivate_account(
        self, data: DeactivateAccountPayload
    ) -> DeactivateAccountResponsePayload:
        """Deactivate a user's account. Requires admin credentials"""
        token, user_details = self._repository.deactivate_account(
            token=data.token, username=data.username
        )
        return DeactivateAccountResponsePayload(
            token=token, user_details=UserDetails(**user_details)
        )

    def confirm_account(self, token: str) -> ConfirmAccountResponsePayload:
        """Path for user to verify their email address"""
        token, user_details = self._repository.confirm_account(token)
        return ConfirmAccountResponsePayload(
            token=token, user_details=UserDetails(**user_details)
        )
