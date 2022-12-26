from dataclasses import dataclass
from typing import Literal

from abstract_domain_model.models.accounts import UserDetails


@dataclass(frozen=True)
class DeactivateAccount:
    type: Literal["DEACTIVATE_ACCOUNT"]
    payload: "DeactivateAccountPayload"


@dataclass(frozen=True)
class DeactivateAccountPayload:
    token: str
    username: str


@dataclass(frozen=True)
class DeactivateAccountResponse:
    type: Literal["DEACTIVATE_ACCOUNT_RESPONSE"]
    payload: "DeactivateAccountResponsePayload"


@dataclass(frozen=True)
class DeactivateAccountResponsePayload:
    token: str
    user_details: UserDetails
