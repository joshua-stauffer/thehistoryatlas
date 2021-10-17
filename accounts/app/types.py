from typing import TypedDict

Token = str
UserId = str

class UserDetails(TypedDict):
    """A dict representing all queriable user details"""

    f_name: str
    l_name: str
    email: str
    username: str
    last_login: str
