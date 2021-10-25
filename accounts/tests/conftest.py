from datetime import datetime
from datetime import timedelta
from cryptography.fernet import Fernet
import pytest
from sqlalchemy.orm import Session
from app.database import Database
from app.encryption import get_token
from app.encryption import fernet
from app.encryption import TTL
from app.schema import User

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False


@pytest.fixture
def db():
    c = Config()
    return Database(c)

@pytest.fixture
def user_details():
    return {
        'id': 'a32fb4ef-5e18-4394-8f2b-473e738fdef1',
        'email': 'testemail@thehistoryatlas.org',
        'f_name': 'testy',
        'l_name': 'tester',
        'username': 'testersone',
        'password': 'vivaciously',
    }

@pytest.fixture
def admin_user_details():
    return {
        'id': '8e79f989-7051-4303-895e-c00a55ba927e',
        'email': 'admin@thehistoryatlas.org',
        'f_name': 'admin',
        'l_name': 'user',
        'username': 'admin',
        'password': 'super_secure_password',
        'type': 'admin',
        'confirmed': True
    }


@pytest.fixture
def user_id(user_details):
    return user_details["id"]

@pytest.fixture
def admin_user_id(admin_user_details):
    return admin_user_details["id"]

@pytest.fixture
def loaded_db(db, user_details, admin_user_details):
    with Session(db._engine, future=True) as session:
        session.add(User(**user_details))
        session.add(User(**admin_user_details))
        session.commit()
    return db


@pytest.fixture
def active_token(loaded_db, user_id):
    token = get_token(user_id)
    return token

@pytest.fixture
def active_admin_token(loaded_db, admin_user_id):
    token = get_token(admin_user_id)
    return token

@pytest.fixture
def nearly_expired_token(user_id):
    """This token is nearly expired but within the refresh period and should
    trigger a token refresh"""
    seconds_delta = TTL - 180 # three minutes before expiration
    expire_time = timedelta(seconds=seconds_delta)
    create_time = datetime.utcnow() - expire_time
    print(f"now is {datetime.utcnow()}")
    print(f'create time is {create_time}')
    token_bytes = f"{user_id}|{create_time}".encode()
    return fernet.encrypt(token_bytes)

@pytest.fixture
def expired_token(user_id):
    """this token is no longer valid and should raise an error."""
    seconds_delta = TTL + 180 # three minutes after expiration
    expire_time = timedelta(seconds=seconds_delta)
    create_time = datetime.utcnow() - expire_time
    print(f"now is {datetime.utcnow()}")
    print(f"expire time is {datetime.utcnow() - timedelta(seconds=TTL)}")
    print(f'create time is {create_time}')
    token_bytes = f"{user_id}|{create_time}".encode()
    return fernet.encrypt(token_bytes)

@pytest.fixture
def invalid_token():
    """This token doesn't work."""
    different_key = 'KNpxnpKKUtFRQoQgFWfgKD0raSDSY19jUPu7lymiKrQ='.encode()
    f = Fernet(different_key)
    user_id = '0056428d-f20f-4914-8196-a191d41d375f'
    token_bytes = f"{user_id}|{datetime.utcnow()}".encode()
    return f.encrypt(token_bytes)