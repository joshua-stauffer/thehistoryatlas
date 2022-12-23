from dataclasses import dataclass
from typing import Literal

from abstract_domain_model.models.accounts.credentials import Credentials


@dataclass(frozen=True)
class Login:
    type: Literal["LOGIN"]
    payload: Credentials


@dataclass(frozen=True)
class LoginResponse:
    type: Literal["LOGIN_RESPONSE"]
    payload: "LoginResponsePayload"


@dataclass(frozen=True)
class LoginResponsePayload:
    success: bool
