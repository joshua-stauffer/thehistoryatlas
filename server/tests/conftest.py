import os
from copy import deepcopy
from datetime import timedelta, datetime
from typing import List, Dict

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from the_history_atlas.apps.accounts.database import Database as AccountsDB
from the_history_atlas.apps.accounts.encryption import encrypt, get_token, TTL, fernet
from the_history_atlas.apps.accounts.schema import Base, User

from the_history_atlas.apps.config import Config
from the_history_atlas.apps.writemodel.state_manager.database import (
    Database as WriteModelDB,
)
from the_history_atlas.apps.writemodel.state_manager.schema import Base, GUID


@pytest.fixture
def config():
    config = Config()
    TEST_DB_URI = os.environ.get("TEST_DB_URI", None)
    if not TEST_DB_URI:
        raise Exception("Env variable `TEST_DB_URI` must be set to run test suite.")
    config.DB_URI = TEST_DB_URI
    config.DEBUG = False
    config.TESTING = True
    return config


@pytest.fixture
def engine(config):
    return create_engine(config.DB_URI, echo=config.DEBUG, future=True)


@pytest.fixture
def accounts_bare_db(engine):

    db = AccountsDB(engine=engine)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return db


@pytest.fixture
def accounts_db(accounts_bare_db, admin_user_details, engine):
    """An active database instance with one admin user"""
    # must start with an admin user
    encrypted_admin_details = {
        **admin_user_details,
        "password": encrypt(admin_user_details["password"]).decode(),
    }
    with Session(engine, future=True) as session:
        session.add(User(**encrypted_admin_details))
        session.commit()
    return accounts_bare_db


@pytest.fixture
def accounts_loaded_db(accounts_db, user_details, unconfirmed_user, engine):
    """An active database instance with two users -- one admin, one contrib"""
    encrypted_user_details = {
        **user_details,
        "password": encrypt(user_details["password"]).decode(),
    }
    unconfirmed_user_details = {
        **unconfirmed_user,
        "password": encrypt(unconfirmed_user["password"]).decode(),
    }
    with Session(engine, future=True) as session:
        session.add(User(**encrypted_user_details))
        session.add(User(**unconfirmed_user_details))
        session.commit()
    return accounts_db


@pytest.fixture
def user_details():
    return {
        "id": "a32fb4ef-5e18-4394-8f2b-473e738fdef1",
        "email": "testemail@thehistoryatlas.org",
        "f_name": "testy",
        "l_name": "tester",
        "username": "testersone",
        "password": "vivaciously",
        "confirmed": True,
        "deactivated": False,
    }


@pytest.fixture
def unconfirmed_user():
    return {
        "id": "76586111-aaf1-4c3d-8cf5-2d55fca19977",
        "email": "another_test_email@thehistoryatlas.org",
        "f_name": "freethrow",
        "l_name": "shooter",
        "username": "swoop",
        "password": "nothing-but-net",
        "confirmed": False,
        "deactivated": False,
    }


@pytest.fixture
def unconfirmed_user_id(unconfirmed_user):
    return unconfirmed_user["id"]


@pytest.fixture
def other_user_details():
    return {
        "email": "test@thehistoryatlas.org",
        "f_name": "another",
        "l_name": "tester",
        "username": "the_test_user",
        "password": "test_test_test",
    }


@pytest.fixture
def admin_user_details():
    return {
        "id": "8e79f989-7051-4303-895e-c00a55ba927e",
        "email": "admin@thehistoryatlas.org",
        "f_name": "admin",
        "l_name": "user",
        "username": "admin1",
        "password": "super_secure_password",
        "type": "admin",
        "confirmed": True,
    }


@pytest.fixture
def user_id(user_details):
    return user_details["id"]


@pytest.fixture
def admin_user_id(admin_user_details):
    return admin_user_details["id"]


@pytest.fixture
def active_token(user_id):
    token = get_token(user_id)
    return token


@pytest.fixture
def active_admin_token(admin_user_id):
    token = get_token(admin_user_id)
    return token


@pytest.fixture
def unconfirmed_user_token(unconfirmed_user_id):
    return get_token(unconfirmed_user_id)


@pytest.fixture
def nearly_expired_token(user_id):
    """This token is nearly expired but within the refresh period and should
    trigger a token refresh"""
    seconds_delta = TTL - 180  # three minutes before expiration
    expire_time = timedelta(seconds=seconds_delta)
    create_time = datetime.utcnow() - expire_time
    print(f"now is {datetime.utcnow()}")
    print(f"create time is {create_time}")
    token_bytes = f"{user_id}|{create_time}".encode()
    return fernet.encrypt(token_bytes)


@pytest.fixture
def expired_token(user_id):
    """this token is no longer valid and should raise an error."""
    seconds_delta = TTL + 180  # three minutes after expiration
    expire_time = timedelta(seconds=seconds_delta)
    create_time = datetime.utcnow() - expire_time
    print(f"now is {datetime.utcnow()}")
    print(f"expire time is {datetime.utcnow() - timedelta(seconds=TTL)}")
    print(f"create time is {create_time}")
    token_bytes = f"{user_id}|{create_time}".encode()
    return fernet.encrypt(token_bytes)


@pytest.fixture
def invalid_token():
    """This token doesn't work."""
    different_key = "KNpxnpKKUtFRQoQgFWfgKD0raSDSY19jUPu7lymiKrQ=".encode()
    f = Fernet(different_key)
    user_id = "0056428d-f20f-4914-8196-a191d41d375f"
    token_bytes = f"{user_id}|{datetime.utcnow()}".encode()
    return f.encrypt(token_bytes)


def redact_values(data: Dict, keys: set[str]) -> Dict:
    """Return a copy of data with param keys redacted"""
    data = deepcopy(data)
    REDACTED = "<REDACTED>"

    def recursively_redact(d):
        nonlocal REDACTED, keys

        if isinstance(d, dict):
            for k, v in d.items():
                if k in keys:
                    d[k] = REDACTED
                elif isinstance(v, dict):
                    recursively_redact(v)
                elif isinstance(v, list):
                    for i in v:
                        recursively_redact(i)
        elif isinstance(d, list):
            for i in d:
                recursively_redact(i)

    recursively_redact(data)
    return data


@pytest.fixture
def writemodel_db(
    engine,
    existing_summary_id,
    existing_meta_id,
    existing_time_id,
    existing_place_id,
    existing_person_id,
):
    db = WriteModelDB(database_client=engine, stm_timeout=0)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine, future=True) as session:
        session.add_all(
            [
                GUID(value=existing_summary_id, type="SUMMARY"),
                GUID(value=existing_meta_id, type="META"),
                GUID(value=existing_person_id, type="PERSON"),
                GUID(value=existing_place_id, type="PLACE"),
                GUID(value=existing_time_id, type="TIME"),
            ]
        )
        session.commit()

    yield db

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)