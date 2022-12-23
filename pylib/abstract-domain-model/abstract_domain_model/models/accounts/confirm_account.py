from dataclasses import dataclass
from typing import Literal

from abstract_domain_model.models.accounts import UserDetails


@dataclass(frozen=True)
class ConfirmAccount:
    type: Literal["CONFIRM_ACCOUNT"]
    payload: "ConfirmAccountPayload"


@dataclass(frozen=True)
class ConfirmAccountPayload:
    token: str


@dataclass(frozen=True)
class ConfirmAccountResponse:
    type: Literal["CONFIRM_ACCOUNT_RESPONSE"]
    payload: "ConfirmAccountResponsePayload"


@dataclass(frozen=True)
class ConfirmAccountResponsePayload:
    token: str
    user_details: UserDetails
