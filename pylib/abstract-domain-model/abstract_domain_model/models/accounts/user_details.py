from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UserDetails:
    f_name: str
    l_name: str
    username: str
    email: str
    last_login: str
    type: Literal["admin", "contrib"]
