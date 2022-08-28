from datetime import datetime, timedelta
import os
from typing import Union
import logging
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from accounts.types import Token
from accounts.types import UserId
from accounts.errors import ExpiredTokenError
from accounts.errors import InvalidTokenError


logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


SEC_KEY = os.environ.get("SEC_KEY", None)
TTL = os.environ.get("TTL", None)
REFRESH_BY = os.environ.get("REFRESH_BY", None)
if not (TTL and SEC_KEY and REFRESH_BY):
    raise Exception("Missing environment variables for the encryption utility.")
try:
    TTL = int(TTL)
except ValueError:
    raise Exception("TTL environment variable must be parsable as integer.")
try:
    REFRESH_BY = int(REFRESH_BY)
except ValueError:
    raise Exception("REFRESH_BY environment variable must be parsable as integer.")

fernet = Fernet(SEC_KEY)


def encrypt(password: str) -> bytes:
    """encrypts sensitive user data"""

    byte_password = password.encode()
    encrypted_password = fernet.encrypt(byte_password)
    return encrypted_password


def check_password(password, encrypted_password) -> bool:
    return password.encode() == fernet.decrypt(encrypted_password)


def get_token(user_id) -> Token:
    """obtain a cryptographically secure token"""

    token_bytes = f"{user_id}|{datetime.utcnow()}".encode()
    return str(fernet.encrypt(token_bytes).decode())


def validate_token(
    token: Union[str, bytes], force_refresh=False
) -> Tuple[UserId, Token]:
    """Checks if token has expired and returns a user id or raises an exception"""
    if isinstance(token, str):
        token = token.encode()
    elif isinstance(token, bytes):
        pass
    else:
        raise InvalidTokenError("Token must be string or bytes")
    try:
        token_str = fernet.decrypt(token, ttl=TTL).decode()
    except InvalidToken:
        raise InvalidTokenError
    user_id, create_time = parse_token_str(token_str)
    if create_time < datetime.utcnow() - timedelta(seconds=TTL):
        raise ExpiredTokenError
    refresh_time = create_time + timedelta(seconds=REFRESH_BY)
    if refresh_time < datetime.utcnow():
        log.debug("Token close to expiration - returning new token.")
        token = get_token(user_id)
    elif force_refresh:
        token = get_token(user_id)
    if isinstance(token, bytes):
        token = token.decode()
    return user_id, str(token)


def parse_token_str(token_str: str) -> Tuple[UserId, datetime]:
    split_token = token_str.split("|")
    user_id = split_token[0]
    time_ = str_to_time(split_token[1])
    return user_id, time_


def str_to_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
