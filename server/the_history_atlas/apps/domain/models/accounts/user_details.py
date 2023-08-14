from dataclasses import dataclass


@dataclass(frozen=True)
class UserDetails:
    f_name: str
    l_name: str
    username: str
    email: str
    last_login: str
