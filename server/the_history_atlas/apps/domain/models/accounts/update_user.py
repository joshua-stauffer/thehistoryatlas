from dataclasses import dataclass
from typing import Literal, Optional, Dict

from the_history_atlas.apps.domain.models.accounts.credentials import Credentials
from the_history_atlas.apps.domain.models.accounts.user_details import UserDetails


@dataclass(frozen=True)
class UpdateUser:
    type: Literal["UPDATE_USER"]
    payload: "UpdateUserPayload"


@dataclass(frozen=True)
class UpdateUserPayload:
    user_details: Dict
    token: str
    credentials: Optional[Credentials]


@dataclass(frozen=True)
class UpdateUserResponse:
    type: Literal["UPDATE_USER_RESPONSE"]
    payload: "UpdateUserResponsePayload"


@dataclass(frozen=True)
class UpdateUserResponsePayload:
    token: str
    user_details: UserDetails
