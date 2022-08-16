import os
from unittest.mock import MagicMock

import pytest

from writemodel.state_manager.database import Database
from writemodel.state_manager.schema import Base


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def db():

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

    return db
