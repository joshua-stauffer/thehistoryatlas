import logging
from dataclasses import asdict
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.engine import Engine

from the_history_atlas.apps.accounts.errors import (
    MissingUserError,
    DeactivatedUserError,
    AuthenticationError,
    UnconfirmedUserError,
)
from the_history_atlas.apps.config import Config

from the_history_atlas.apps.accounts.api_keys import ApiKeyRepository
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
        self._api_key_repo = ApiKeyRepository(engine=database_client)

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

    def signup(
        self,
        username: str,
        password: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> str:
        """Self-service account creation. Returns a JWT token."""
        token = self._repository.signup(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return token

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

    def get_user_by_id(self, user_id: str) -> GetUserResponsePayload:
        """Get user details by user ID (for API key auth)."""
        _, user_details = self._repository.get_user_by_id(user_id=user_id)
        return GetUserResponsePayload(
            token="api-key-auth",
            user_details=UserDetails(**user_details),
        )

    def get_user_id_from_token(self, token: str) -> str:
        """Extract user_id from a JWT token."""
        return self._repository.get_user_id_by_token(token=token)

    def create_api_key(self, user_id: str, name: str) -> tuple[str, dict]:
        """Create a new API key for a user. Returns (raw_key, record)."""
        return self._api_key_repo.create_api_key(user_id=user_id, name=name)

    def validate_api_key(self, raw_key: str) -> Optional[str]:
        """Validate an API key. Returns user_id if valid, None otherwise."""
        return self._api_key_repo.validate_api_key(raw_key=raw_key)

    def deactivate_api_key(self, key_id: UUID, user_id: str) -> bool:
        """Deactivate an API key. Returns True if deactivated."""
        return self._api_key_repo.deactivate_api_key(key_id=key_id, user_id=user_id)
