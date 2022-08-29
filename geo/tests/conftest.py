import os

import pytest
from sqlalchemy import create_engine

from geo.state.schema import Base


@pytest.fixture
def TEST_DB_URI():
    db_uri = os.environ.get("TEST_DB_URI", None)
    if db_uri is None:
        raise Exception(
            "Environmental variable TEST_DB_URI must be defined to run tests."
        )
    return db_uri


@pytest.fixture
def engine(TEST_DB_URI):
    engine = create_engine(TEST_DB_URI, echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine
