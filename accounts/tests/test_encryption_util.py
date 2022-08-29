import datetime
from uuid import UUID
from base64 import b64decode
import pytest
from unittest import mock
from accounts.errors import ExpiredTokenError
from accounts.errors import InvalidTokenError
from accounts.encryption import encrypt
from accounts.encryption import check_password
from accounts.encryption import get_token
from accounts.encryption import validate_token
from accounts.encryption import parse_token_str
from accounts.encryption import str_to_time
from accounts.encryption import fernet


def test_encrypt():
    value = "some random value"
    encrypted_val = encrypt(value)
    assert value != encrypted_val


def test_check_password():
    password = "not a real password"
    encrypted_password = encrypt(password)
    assert password != encrypted_password
    assert check_password(password, encrypted_password)


def test_get_token():
    user_id = "my_user_id_123"
    token = get_token(user_id)
    new_user_id, new_token = validate_token(token)
    assert user_id == new_user_id
    assert token == new_token


def test_get_token_with_force_refresh():
    user_id = "my_user_id_123"
    token = get_token(user_id)
    new_user_id, new_token = validate_token(token, force_refresh=True)
    assert user_id == new_user_id
    assert token is not new_token


def test_validate_token(active_token, user_details):
    user_id, token = validate_token(active_token)
    assert user_id == user_details["id"]
    assert active_token == token


def test_validate_nearly_expired_token(user_id, nearly_expired_token):
    cur_user_id, token = validate_token(nearly_expired_token)
    assert user_id == cur_user_id
    assert token != nearly_expired_token


def test_expired_token(expired_token):
    with pytest.raises(ExpiredTokenError):
        validate_token(expired_token)


def test_invalid_token(invalid_token):
    with pytest.raises(InvalidTokenError):
        validate_token(invalid_token)


def test_parse_token_str(active_token):
    token = active_token.encode()
    token_str = fernet.decrypt(token).decode()
    user_id, time_ = parse_token_str(token_str)
    assert UUID(user_id), "This user_id should be a valid UUID"
    assert isinstance(time_, datetime.datetime)


def test_str_to_time():
    now = str(datetime.datetime.utcnow())
    time_ = str_to_time(now)
    assert isinstance(time_, datetime.datetime)
