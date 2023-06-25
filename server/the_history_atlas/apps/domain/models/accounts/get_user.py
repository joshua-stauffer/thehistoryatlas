from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.accounts.user_details import UserDetails


@dataclass(frozen=True)
class GetUser:
    type: Literal["GET_USER"]
    payload: "GetUserPayload"


@dataclass(frozen=True)
class GetUserPayload:
    token: str


@dataclass(frozen=True)
class GetUserResponse:
    type: Literal["GET_USER_RESPONSE"]
    payload: "GetUserResponsePayload"


@dataclass(frozen=True)
class GetUserResponsePayload:
    token: str
    user_details: UserDetails
