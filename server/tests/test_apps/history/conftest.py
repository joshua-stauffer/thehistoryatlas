from typing import Generator, Callable
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy import text

from the_history_atlas.apps.history import HistoryApp
from the_history_atlas.apps.history.repository import Repository
from the_history_atlas.apps.history.trie import Trie


@pytest.fixture
def mock_db():
    return MagicMock(spec=Repository)


@pytest.fixture
def history_app(engine, config):
    return HistoryApp(database_client=engine, config_app=config)


@pytest.fixture
def history_db(engine):
    source_trie = Trie()
    database = Repository(
        database_client=engine,
        source_trie=source_trie,
    )
    source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
    return database


@pytest.fixture
def source_title():
    return "Source Title"


@pytest.fixture
def source_author():
    return "Source Author"


@pytest.fixture
def cleanup_tag(history_db) -> Generator[Callable[[UUID], None], None, None]:
    tags_to_cleanup: set[UUID] = set()

    def _cleanup(tag_id: UUID) -> None:
        tags_to_cleanup.add(tag_id)

    yield _cleanup
    if not tags_to_cleanup:
        return  # don't error on an empty tuple
    with history_db.Session() as session:
        # Cleanup in the correct order to handle foreign key constraints
        session.execute(
            text(
                """
                -- Delete related tag instances first
                DELETE FROM tag_instances WHERE tag_id IN :ids;
                
                -- Delete related records based on tag type
                DELETE FROM times WHERE id IN :ids;
                DELETE FROM places WHERE id IN :ids;
                DELETE FROM people WHERE id IN :ids;
                
                -- Delete story names and tag names
                DELETE FROM story_names WHERE tag_id IN :ids;
                DELETE FROM tag_names WHERE tag_id IN :ids;
                
                -- Finally, delete the tags
                DELETE FROM tags WHERE id IN :ids;
                """
            ),
            {"ids": tuple(tags_to_cleanup)},
        )
        session.commit()
