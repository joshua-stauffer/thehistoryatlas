import os
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from server.the_history_atlas.apps.writemodel import Database
from server.the_history_atlas.apps.writemodel import Base, GUID


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def db(
    existing_summary_id,
    existing_meta_id,
    existing_time_id,
    existing_place_id,
    existing_person_id,
):

    TEST_DB_URI = os.environ.get("TEST_DB_URI", None)
    if not TEST_DB_URI:
        raise Exception("Env variable `TEST_DB_URI` must be set to run test suite.")

    class Config:
        """minimal class for setting up an in memory db for this test"""

        def __init__(self):
            self.DB_URI = TEST_DB_URI
            self.DEBUG = False

    config = Config()
    db = Database(config, stm_timeout=0)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(db._engine)
    Base.metadata.create_all(db._engine)

    with Session(db._engine, future=True) as session:
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

    return db


@pytest.fixture
def existing_summary_id():
    return "b73eb1f4-756a-445c-addb-c56ac2bb1fe5"


@pytest.fixture
def existing_meta_id():
    return "f7bb4de9-1b5b-4b89-a955-afd32ed70cfd"


@pytest.fixture
def existing_time_id():
    return "728ac243-48d4-453c-a120-56d9e0176c7c"


@pytest.fixture
def existing_person_id():
    return "cb08564a-8021-4491-ac7b-b8684d9b9297"


@pytest.fixture
def existing_place_id():
    return "a54d1a83-0685-4f1b-bf4e-abaae4e159a5"
