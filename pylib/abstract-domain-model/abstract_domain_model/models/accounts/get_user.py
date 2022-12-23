from dataclasses import dataclass
from typing import Literal

from abstract_domain_model.models.accounts import UserDetails


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
