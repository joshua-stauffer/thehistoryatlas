from base64 import b64decode
from unittest import mock
from app.encryption import encrypt
from app.encryption import check_password
from app.encryption import get_token
from app.encryption import validate_token
from app.encryption import parse_token_str

def test_password():

    password = "not a real password"
    encrypted_password = encrypt(password)
    assert password != encrypted_password
    assert check_password(password, encrypted_password)

def test_token():
    user_id = 'my_user_id_123'
    token = get_token(user_id)
    new_user_id, new_token = validate_token(token)
    assert user_id == new_user_id
    assert token is new_token
