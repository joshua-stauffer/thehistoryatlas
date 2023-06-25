from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str
