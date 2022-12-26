from dataclasses import dataclass
from typing import Literal

from abstract_domain_model.models.accounts import UserDetails


@dataclass(frozen=True)
class AddUser:
    type: Literal["ADD_USER"]
    payload: "AddUserPayload"


@dataclass(frozen=True)
class AddUserPayload:
    token: str
    user_details: UserDetails
