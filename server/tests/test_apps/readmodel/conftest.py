from typing import Generator, Callable
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy import text

from the_history_atlas.apps.history import HistoryApp
from the_history_atlas.apps.history.database import Database
from the_history_atlas.apps.history.query_handler import QueryHandler
from the_history_atlas.apps.history.trie import Trie


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def readmodel_app(engine, config):
    return HistoryApp(database_client=engine, config_app=config)


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


@pytest.fixture
def cleanup_tag(readmodel_db) -> Generator[Callable[[UUID], None], None, None]:
    tags_to_cleanup: set[UUID] = set()

    def _cleanup(tag_id: UUID) -> None:
        tags_to_cleanup.add(tag_id)

    yield _cleanup
    if not tags_to_cleanup:
        return  # don't error on an empty tuple
    with readmodel_db.Session() as session:
        # cleanup
        session.execute(
            text(
                """
                delete from person where person.id in :ids;
                delete from story_names where story_names.tag_id in :ids;
                delete from tag_name_assoc where tag_name_assoc.tag_id in :ids;
                delete from tags where tags.id in :ids;
                """
            ),
            {"ids": tuple(tags_to_cleanup)},
        )
        session.commit()
