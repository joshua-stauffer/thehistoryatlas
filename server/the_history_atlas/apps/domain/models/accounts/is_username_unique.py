from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class IsUsernameUnique:
    type: Literal["IS_USERNAME_UNIQUE"]
    payload: "IsUsernameUniquePayload"


@dataclass(frozen=True)
class IsUsernameUniquePayload:
    username: str


@dataclass(frozen=True)
class IsUsernameUniqueResponse:
    type: Literal["IS_USERNAME_UNIQUE"]
    payload: "IsUsernameUniqueResponsePayload"


@dataclass(frozen=True)
class IsUsernameUniqueResponsePayload:
    username: str
    is_unique: bool
