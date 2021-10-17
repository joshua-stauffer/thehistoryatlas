from datetime import datetime, timedelta
import os
import logging
from typing import Tuple, get_args
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from app.types import Token
from app.types import UserId
from app.errors import ExpiredTokenError


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)

SEC_KEY = os.environ.get('SEC_KEY')
TTL = int(os.environ.get('TTL'))
REFRESH_BY = int(os.environ.get('REFRESH_BY'))
if not (TTL and SEC_KEY and REFRESH_BY):
    raise Exception('Missing environment variables for the encryption utility.')

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
    return fernet.encrypt(token_bytes)


def validate_token(token) -> Tuple[UserId, Token]:
    """Checks if token has expired and returns a user id or raises an exception"""

    try:
        token_str = fernet.decrypt(token, ttl=TTL).decode()
    except InvalidToken:
        raise ExpiredTokenError
    user_id, create_time = parse_token_str(token_str)
    refresh_time = create_time + timedelta(seconds=REFRESH_BY)
    if refresh_time < datetime.utcnow():
        log.debug('Token close to expiration - returning new token.')
        token = get_token(user_id)
    return user_id, token


def parse_token_str(token_str) -> Tuple[UserId, datetime]:
    split_token = token_str.split('|')
    user_id = split_token[0]
    time_ = str_to_time(split_token[1])
    return user_id, time_


def str_to_time(time_str: str) -> datetime:
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')