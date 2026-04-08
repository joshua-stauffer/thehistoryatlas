import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from the_history_atlas.apps.history.repository import Repository
from the_history_atlas.apps.history.trie import Trie
from the_history_atlas.apps.history.schema import Base, Name, Tag, tag_names
from the_history_atlas.apps.domain.models.history.get_fuzzy_search_by_name import (
    FuzzySearchByName,
)
from uuid import uuid4


@pytest.fixture
def db_uri():
    uri = os.environ.get("THA_DB_URI")
    if not uri:
        pytest.skip("THA_DB_URI environment variable not set")
    return uri


@pytest.fixture
def db_client(db_uri):
    engine = create_engine(db_uri)

    # Create necessary extensions and indices if they don't exist
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_names_trgm_gin 
                ON names USING GIN (name gin_trgm_ops);
            """
                )
            )

    return engine  # The DatabaseClient is just an alias for Engine


@pytest.fixture
def repository(db_client):
    # Create an empty trie - it won't be used
    source_trie = Trie()
    return Repository(database_client=db_client, source_trie=source_trie)


@pytest.fixture
def test_data(repository):
    Session = repository.Session

    # Store the created IDs for cleanup
    created_tag_ids = []
    created_name_ids = []

    # Create test data
    with Session() as session:
        # Add test names and tags
        test_entries = [
            ("Alexander the Great", "PERSON"),
            ("Alexander Hamilton", "PERSON"),
            ("Alexandria, Egypt", "PLACE"),
            ("Great Wall of China", "PLACE"),
            ("Alexandretta", "PLACE"),
        ]

        for name_str, tag_type in test_entries:
            # Create tag
            tag_id = uuid4()
            created_tag_ids.append(tag_id)
            tag = Tag(id=tag_id, type=tag_type)
            session.add(tag)

        # Commit the tags first to satisfy foreign key constraints
        session.commit()

        # Now add names and tag_name associations
        for i, (name_str, _) in enumerate(test_entries):
            # Create name
            name_id = uuid4()
            created_name_ids.append(name_id)
            name = Name(id=name_id, name=name_str)
            session.add(name)

            # Need to commit names before creating associations
            session.commit()

            # Associate name with tag
            session.execute(
                text(
                    """
                    INSERT INTO tag_names (tag_id, name_id)
                    VALUES (:tag_id, :name_id)
                """
                ),
                {"tag_id": created_tag_ids[i], "name_id": name_id},
            )

        session.commit()

    yield

    # Clean up test data
    with Session() as session:
        # Delete associations first
        for name_id in created_name_ids:
            session.execute(
                text("DELETE FROM tag_names WHERE name_id = :name_id"),
                {"name_id": name_id},
            )
        session.commit()

        # Delete names
        for name_id in created_name_ids:
            session.execute(text("DELETE FROM names WHERE id = :id"), {"id": name_id})
        session.commit()

        # Delete tags
        for tag_id in created_tag_ids:
            session.execute(text("DELETE FROM tags WHERE id = :id"), {"id": tag_id})
        session.commit()


def test_fuzzy_search_exact_match(repository, test_data):
    """Test that fuzzy search returns exact matches."""
    results = repository.get_name_by_fuzzy_search("Alexander")

    # Check that we get results containing "Alexander"
    assert len(results) > 0

    # All results should contain "Alexander" or be similar
    alexander_matches = [r for r in results if "Alexander" in r.name]
    assert len(alexander_matches) > 0


def test_fuzzy_search_partial_match(repository, test_data):
    """Test that fuzzy search returns partial matches."""
    results = repository.get_name_by_fuzzy_search("Alex")

    # Check that we get results starting with "Alex"
    assert len(results) > 0

    # Some results should contain "Alex"
    alex_matches = [r for r in results if "Alex" in r.name]
    assert len(alex_matches) > 0


def test_fuzzy_search_misspelling(repository, test_data):
    """Test that fuzzy search handles misspellings."""
    # Misspelling "Alexander" as "Aleksander"
    results = repository.get_name_by_fuzzy_search("Aleksander")

    # Should still find Alexander entries despite misspelling
    assert len(results) > 0

    # Should have "Alexander" in results despite misspelling
    alexander_matches = [r for r in results if "Alexander" in r.name]
    assert len(alexander_matches) > 0


def test_fuzzy_search_returns_ids(repository, test_data):
    """Test that fuzzy search returns proper IDs for matched names."""
    results = repository.get_name_by_fuzzy_search("Alexander")

    # Check that IDs are returned
    assert len(results) > 0
    for result in results:
        assert isinstance(result, FuzzySearchByName)
        assert hasattr(result, "ids")
        assert len(result.ids) > 0
        # Each ID should be a UUID
        for id in result.ids:
            assert isinstance(id, uuid.UUID)


def test_fuzzy_search_empty_query(repository, test_data):
    """Test that fuzzy search returns empty list for empty query."""
    results = repository.get_name_by_fuzzy_search("")
    assert results == []


def test_fuzzy_search_no_match(repository, test_data):
    """Test that fuzzy search returns empty list for non-matching query."""
    results = repository.get_name_by_fuzzy_search("xyznonexistentquery")
    assert len(results) == 0
