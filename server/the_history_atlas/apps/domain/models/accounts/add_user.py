from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.accounts.user_details import UserDetails


@dataclass(frozen=True)
class AddUser:
    type: Literal["ADD_USER"]
    payload: "AddUserPayload"


@dataclass(frozen=True)
class AddUserPayload:
    token: str
    user_details: UserDetails
