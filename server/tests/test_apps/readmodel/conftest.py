from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from tests.db_builder import DBBuilder
from tests.seed.readmodel import CITATIONS, SUMMARIES, SOURCES
from the_history_atlas.apps.readmodel import ReadModelApp
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.query_handler import QueryHandler


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def readmodel_app(engine, config):
    return ReadModelApp(database_client=engine, config_app=config)


@pytest.fixture
def readmodel_db(engine):

    db = Database(database_client=engine)

    return db


@pytest.fixture
def source_title():
    return "Source Title"


@pytest.fixture
def source_author():
    return "Source Author"


@pytest.fixture
def query_handler(db_tuple):
    db, _ = db_tuple
    return QueryHandler(database_instance=db)
