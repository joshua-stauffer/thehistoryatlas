from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from tests.db_builder import DBBuilder
from tests.seed.readmodel import CITATIONS, SUMMARIES, SOURCES
from the_history_atlas.apps.readmodel import ReadModelApp
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.query_handler import QueryHandler
from the_history_atlas.apps.readmodel.trie import Trie


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def readmodel_app(engine, config):
    return ReadModelApp(database_client=engine, config_app=config)


@pytest.fixture
def readmodel_db(engine):
    source_trie = Trie()
    entity_trie = Trie()
    database = Database(
        database_client=engine, source_trie=source_trie, entity_trie=entity_trie
    )
    source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
    entity_trie.build(entity_tuples=database.get_all_entity_names())
    return database


@pytest.fixture
def source_title():
    return "Source Title"


@pytest.fixture
def source_author():
    return "Source Author"


@pytest.fixture
def query_handler(engine):
    source_trie = Trie()
    entity_trie = Trie()
    database = Database(
        database_client=engine, source_trie=source_trie, entity_trie=entity_trie
    )
    source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
    entity_trie.build(entity_tuples=database.get_all_entity_names())
    return QueryHandler(
        database_instance=database,
        source_trie=source_trie,
        entity_trie=entity_trie,
    )
