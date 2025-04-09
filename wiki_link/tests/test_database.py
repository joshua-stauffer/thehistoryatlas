from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

import pytest
from wiki_service.database import Database, Item
from wiki_service.schema import IDLookup, WikiQueue, Config, FactoryResult
from wiki_service.types import EntityType, WikiDataItem
from sqlalchemy import create_engine, text


@pytest.fixture
def engine(config):
    return create_engine(config.DB_URI, echo=config.DEBUG, future=True)


@pytest.fixture
def wiki_id() -> str:
    return "Q937"


@pytest.fixture
def local_id() -> str:
    return UUID("4e42b20e-838c-4808-9353-b20ec80e6e54")


@pytest.fixture
def seed_id_lookup(engine, wiki_id: str, local_id: UUID):
    with Session(engine, future=True) as session:
        session.execute(
            text(
                """
                delete from id_lookup where wiki_id = :wiki_id;
            """
            ),
            {"wiki_id": wiki_id},
        )
        session.add(
            IDLookup(
                wiki_id=wiki_id,
                entity_type="PERSON",
                local_id=local_id,
                last_checked="2023-01-19 19:14:35",
                last_modified_at="2023-01-19 19:14:35",
            )
        )
        session.commit()
    yield
    with Session(engine, future=True) as session:
        session.execute(
            text(
                """
                delete from id_lookup where wiki_id = :wiki_id;
            """
            ),
            {"wiki_id": wiki_id},
        )
        session.commit()


def test_wiki_id_exists_with_non_existent_id(config):
    db = Database(config=config)
    not_an_id = "4c993806-5616-4d91-bb6e-05a59f21ab70"
    assert db.wiki_id_exists(wiki_id=not_an_id) is False


def test_wiki_id_exists_with_real_id(config, seed_id_lookup, wiki_id: str):
    db = Database(config=config)
    assert db.wiki_id_exists(wiki_id=wiki_id) is True


def test_add_wiki_entry(config, wiki_id: str):
    db = Database(config=config)
    entity_type: EntityType = "PERSON"
    last_modified_at = datetime(2023, 1, 19, 19, 41, 54, tzinfo=timezone.utc)
    db.add_wiki_entry(
        wiki_id=wiki_id,
        entity_type=entity_type,
        last_modified_at=last_modified_at,
    )
    with Session(db._engine, future=True) as session:
        row = session.query(IDLookup).filter(IDLookup.wiki_id == wiki_id).one()
        assert row.wiki_id == wiki_id
        assert row.entity_type == entity_type
        assert row.last_modified_at == last_modified_at
        assert row.last_checked > last_modified_at
        assert row.local_id is None
        session.delete(row)
        session.commit()


def test_add_local_id(config, seed_id_lookup, local_id, wiki_id: str):
    db = Database(config=config)
    db.correlate_local_id_to_wiki_id(wiki_id=wiki_id, local_id=local_id)
    with Session(db._engine, future=True) as session:
        row = session.query(IDLookup).filter(IDLookup.wiki_id == wiki_id).one()
        assert row.local_id == local_id
        session.delete(row)
        session.commit()


def test_add_ids_to_queue(config):
    db = Database(config=config)

    entity_type: EntityType = "PERSON"
    items = [
        WikiDataItem(
            url="https://www.wikidata.org/wiki/Q1339",
            qid="Q1339",
        ),
        WikiDataItem(
            url="https://www.wikidata.org/wiki/Q1340",
            qid="Q1340",
        ),
    ]

    db.add_items_to_queue(entity_type=entity_type, items=items)
    with Session(db._engine, future=True) as session:
        for item in items:
            row = session.query(WikiQueue).filter(WikiQueue.wiki_id == item.qid).one()
            assert row.entity_type == entity_type
            assert row.errors == {}
            session.delete(row)
        session.commit()


def test_get_oldest_item_from_queue(config):
    db = Database(config=config)
    id_times = [
        ("Q5", "2023-01-19 22:10:42"),
        ("Q4", "2022-01-19 22:10:42"),
        ("Q3", "2021-01-19 22:10:42"),
        ("Q2", "2021-01-10 22:10:42"),
        ("Q1", "2020-01-19 22:10:42"),
    ]
    with Session(db._engine, future=True) as session:
        items = [
            WikiQueue(wiki_id=id, time_added=time, entity_type="PERSON")
            for id, time in id_times
        ]
        session.add_all(items)
        session.commit()

    for id, time in sorted(id_times):
        item = db.get_oldest_item_from_queue()
        assert isinstance(item, Item)
        assert item.wiki_id == id
        with Session(db._engine, future=True) as session:
            row = session.query(WikiQueue).filter(WikiQueue.wiki_id == id).one()
            session.delete(row)
            session.commit()

    none = db.get_oldest_item_from_queue()
    assert none is None


def test_remove_item_from_queue_doesnt_error_on_empty_queue(config):
    db = Database(config=config)
    db.remove_item_from_queue(wiki_id="not an id")


def test_remove_item_from_queue(config):
    db = Database(config=config)
    entity_type: EntityType = "PERSON"
    wiki_id = "Q1"
    time_added = "2023-01-19 22:26:35"
    with Session(db._engine, future=True) as session:
        session.add(
            WikiQueue(
                wiki_id=wiki_id,
                entity_type=entity_type,
                time_added=time_added,
            )
        )
        session.commit()

    db.remove_item_from_queue(wiki_id=wiki_id)

    with Session(db._engine, future=True) as session:
        row = (
            session.query(WikiQueue).filter(WikiQueue.wiki_id == wiki_id).one_or_none()
        )
        assert row is None


def test_report_queue_error(config):
    db = Database(config=config)
    entity_type: EntityType = "PERSON"
    wiki_id = "Q1"
    time_added = "2023-01-19 22:26:35"
    with Session(db._engine, future=True) as session:
        session.add(
            WikiQueue(
                wiki_id=wiki_id,
                entity_type=entity_type,
                time_added=time_added,
            )
        )
        try:
            session.commit()
        except Exception as e:
            pass
    error_times = ["2023-01-15 22:26:35", "2023-01-16 22:26:35", "2023-01-17 22:26:35"]

    error = "something didnt work"

    for time in error_times:
        db.report_queue_error(wiki_id=wiki_id, error_time=time, errors=error)

    with Session(db._engine, future=True) as session:
        row = session.query(WikiQueue).filter(WikiQueue.wiki_id == wiki_id).one()
        assert list(row.errors.keys()) == error_times
        for time in error_times:
            assert row.errors[time] == error

        session.delete(row)
        session.commit()


def test_upsert_created_event_new_row(config):
    """Test creating a new CreatedEvents row"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    factory_version = 1
    errors = {"error1": "test error"}

    # Create new row
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
        errors=errors,
    )

    # Verify row was created correctly
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        assert row.wiki_id == wiki_id
        assert row.factory_label == factory_label
        assert row.factory_version == factory_version
        assert row.errors == errors

        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_upsert_created_event_update_row(config):
    """Test updating an existing CreatedEvents row"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    initial_version = 1
    updated_version = 2
    initial_errors = {"error1": "test error"}
    updated_errors = {"error2": "new error"}

    # Create initial row
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=initial_version,
        errors=initial_errors,
    )

    # Update the row
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=updated_version,
        errors=updated_errors,
    )

    # Verify row was updated correctly
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        assert row.wiki_id == wiki_id
        assert row.factory_label == factory_label
        assert row.factory_version == updated_version
        assert row.errors == updated_errors

        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_upsert_created_event_no_errors(config):
    """Test creating a row without errors"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    factory_version = 1

    # Create row without errors
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
    )

    # Verify row was created correctly
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        assert row.wiki_id == wiki_id
        assert row.factory_label == factory_label
        assert row.factory_version == factory_version
        assert row.errors == {}

        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_event_exists_matching_row(config):
    """Test event_exists returns True when a matching row exists"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    factory_version = 1
    errors = {"error1": "test error"}

    # Create a row
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
        errors=errors,
    )

    # Check that event_exists returns True
    assert (
        db.event_exists(
            wiki_id=wiki_id,
            factory_label=factory_label,
            factory_version=factory_version,
        )
        is True
    )

    # Clean up
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_event_exists_no_matching_row(config):
    """Test event_exists returns False when no matching row exists"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    factory_version = 1

    # Check that event_exists returns False for non-existent row
    assert (
        db.event_exists(
            wiki_id=wiki_id,
            factory_label=factory_label,
            factory_version=factory_version,
        )
        is False
    )


def test_event_exists_different_version(config):
    """Test event_exists returns False when row exists but version differs"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    initial_version = 1
    different_version = 2

    # Create a row with initial version
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=initial_version,
    )

    # Check that event_exists returns False for different version
    assert (
        db.event_exists(
            wiki_id=wiki_id,
            factory_label=factory_label,
            factory_version=different_version,
        )
        is False
    )

    # Clean up
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_event_exists_different_factory(config):
    """Test event_exists returns False when row exists but factory differs"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    different_factory = "other_factory"
    factory_version = 1

    # Create a row with initial factory
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
    )

    # Check that event_exists returns False for different factory
    assert (
        db.event_exists(
            wiki_id=wiki_id,
            factory_label=different_factory,
            factory_version=factory_version,
        )
        is False
    )

    # Clean up
    with Session(db._engine, future=True) as session:
        row = (
            session.query(FactoryResult).filter(FactoryResult.wiki_id == wiki_id).one()
        )
        # Clean up - delete created_events first due to foreign key constraint
        session.execute(
            text(
                """
                delete from created_events
                where factory_result_id = :factory_result_id
                """
            ),
            {"factory_result_id": row.id},
        )
        session.delete(row)
        session.commit()


def test_get_server_id_by_event_label_no_matches(config):
    """Test when no matches are found"""
    db = Database(config=config)
    result = db.get_server_id_by_event_label(
        event_labels=["nonexistent_label"],
        primary_entity_id="Q12345",
    )
    assert result == []


def test_get_server_id_by_event_label_with_matches(config):
    """Test when matches are found with various combinations"""
    db = Database(config=config)
    wiki_id = "Q12345"
    secondary_id = "Q67890"
    factory_label = "test_factory"
    factory_version = 1
    server_id = UUID("4e42b20e-838c-4808-9353-b20ec80e6e54")

    # Create test data
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
        server_id=server_id,
    )

    # Test with matching primary entity only
    result = db.get_server_id_by_event_label(
        event_labels=[factory_label],
        primary_entity_id=wiki_id,
    )
    assert result == [server_id]

    # Create another event with secondary entity
    server_id2 = UUID("5f53c31f-949d-5919-a464-c31fc91f7f65")
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
        server_id=server_id2,
        secondary_wiki_id=secondary_id,
    )

    # Test with both primary and secondary entity
    result = db.get_server_id_by_event_label(
        event_labels=[factory_label],
        primary_entity_id=wiki_id,
        secondary_entity_id=secondary_id,
    )
    assert result == [server_id2]

    # Test with multiple event labels
    result = db.get_server_id_by_event_label(
        event_labels=[factory_label, "another_label"],
        primary_entity_id=wiki_id,
    )
    assert sorted(result) == sorted([server_id, server_id2])

    # Clean up
    with Session(db._engine, future=True) as session:
        session.execute(
            text(
                """
                DELETE FROM created_events WHERE primary_entity_id = :wiki_id;
                DELETE FROM factory_results WHERE wiki_id = :wiki_id;
                """
            ),
            {"wiki_id": wiki_id},
        )
        session.commit()


def test_get_server_id_by_event_label_null_server_ids(config):
    """Test that null server_ids are not included in results"""
    db = Database(config=config)
    wiki_id = "Q12345"
    factory_label = "test_factory"
    factory_version = 1

    # Create event without server_id
    db.upsert_created_event(
        wiki_id=wiki_id,
        factory_label=factory_label,
        factory_version=factory_version,
    )

    result = db.get_server_id_by_event_label(
        event_labels=[factory_label],
        primary_entity_id=wiki_id,
    )
    assert result == []

    # Clean up
    with Session(db._engine, future=True) as session:
        session.execute(
            text(
                """
                DELETE FROM created_events WHERE primary_entity_id = :wiki_id;
                DELETE FROM factory_results WHERE wiki_id = :wiki_id;
                """
            ),
            {"wiki_id": wiki_id},
        )
        session.commit()


def test_get_wiki_ids_in_queue_empty_input(config):
    db = Database(config=config)
    assert db.get_wiki_ids_in_queue([]) == set()


def test_get_wiki_ids_in_queue_no_matches(config):
    db = Database(config=config)
    wiki_ids = ["Q1", "Q2", "Q3"]
    assert db.get_wiki_ids_in_queue(wiki_ids) == set()


def test_get_wiki_ids_in_queue_some_matches(config):
    db = Database(config=config)
    entity_type: EntityType = "PERSON"
    time_added = "2023-01-19 22:26:35"

    # Add some items to the queue
    with Session(db._engine, future=True) as session:
        session.add_all([
            WikiQueue(wiki_id="Q1", entity_type=entity_type, time_added=time_added),
            WikiQueue(wiki_id="Q3", entity_type=entity_type, time_added=time_added),
        ])
        session.commit()

    # Test with a mix of existing and non-existing IDs
    wiki_ids = ["Q1", "Q2", "Q3", "Q4"]
    result = db.get_wiki_ids_in_queue(wiki_ids)
    assert result == {"Q1", "Q3"}

    # Clean up
    with Session(db._engine, future=True) as session:
        session.query(WikiQueue).filter(WikiQueue.wiki_id.in_(["Q1", "Q3"])).delete()
        session.commit()


def test_get_wiki_ids_in_queue_all_matches(config):
    db = Database(config=config)
    entity_type: EntityType = "PERSON"
    time_added = "2023-01-19 22:26:35"

    # Add items to the queue
    wiki_ids = ["Q1", "Q2", "Q3"]
    with Session(db._engine, future=True) as session:
        session.add_all([
            WikiQueue(wiki_id=id, entity_type=entity_type, time_added=time_added)
            for id in wiki_ids
        ])
        session.commit()

    # Test that all IDs are found
    result = db.get_wiki_ids_in_queue(wiki_ids)
    assert result == set(wiki_ids)

    # Clean up
    with Session(db._engine, future=True) as session:
        session.query(WikiQueue).filter(WikiQueue.wiki_id.in_(wiki_ids)).delete()
        session.commit()
