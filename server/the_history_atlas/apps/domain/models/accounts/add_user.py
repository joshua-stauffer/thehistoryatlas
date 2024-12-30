from dataclasses import dataclass
from typing import Literal, Dict

from the_history_atlas.apps.domain.models.accounts import UserDetails


@dataclass(frozen=True)
class AddUser:
    type: Literal["ADD_USER"]
    payload: "AddUserPayload"


@dataclass(frozen=True)
class AddUserPayload:
    token: str
    user_details: Dict


@dataclass(frozen=True)
class AddUserResponsePayload:
    token: str
    user_details: UserDetails
