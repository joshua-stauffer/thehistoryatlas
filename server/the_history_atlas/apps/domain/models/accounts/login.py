from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.accounts import Credentials


@dataclass(frozen=True)
class Login:
    type: Literal["LOGIN"]
    payload: Credentials


@dataclass(frozen=True)
class LoginResponse:
    success: bool
    token: str | None


@dataclass(frozen=True)
class LoginResponsePayload:
    success: bool
