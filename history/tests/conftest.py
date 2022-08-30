import os
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from event_schema.EventSchema import Base, Event
from history_service.database import Database
from seed import EVENTS


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def db():
    TEST_DB_URI = os.environ.get("TEST_DB_URI", None)

    if not TEST_DB_URI:
        raise Exception(
            "Env variable `TEST_DB_URI` must be set to run EventStore test suite."
        )

    class Config:
        """minimal class for setting up an in memory db for this test"""

        def __init__(self):
            self.DB_URI = TEST_DB_URI
            self.DEBUG = False

    config = Config()
    db = Database(config)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(db._engine)
    Base.metadata.create_all(db._engine)

    with Session(db._engine, future=True) as session:
        session.add_all([Event(**event_dict) for event_dict in EVENTS])
        session.commit()

    return db
