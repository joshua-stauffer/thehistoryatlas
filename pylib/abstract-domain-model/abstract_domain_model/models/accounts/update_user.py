from dataclasses import dataclass
from typing import Literal, Optional

from abstract_domain_model.models.accounts import UserDetails, Credentials


@dataclass(frozen=True)
class UpdateUser:
    type: Literal["UPDATE_USER"]
    payload: "UpdateUserPayload"


@dataclass(frozen=True)
class UpdateUserPayload:
    user_details: UserDetails
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
