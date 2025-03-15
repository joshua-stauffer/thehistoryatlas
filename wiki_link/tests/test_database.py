from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

import pytest
from wiki_service.database import Database, Item
from wiki_service.schema import IDLookup, WikiQueue, Config
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
