import os
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from the_history_atlas.apps.eventstore.event_schema import Base
from the_history_atlas.apps.eventstore.database import Database
import pytest


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def db(engine):
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

    db = Database(engine=engine)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine, future=True) as session:
        session.add_all([])
        session.commit()

    return db
