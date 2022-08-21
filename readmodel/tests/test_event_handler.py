import asyncio
from datetime import datetime
import json
import pytest
from uuid import uuid4
import random
from sqlalchemy import select
from sqlalchemy.orm import Session

from abstract_domain_model.errors import UnknownMessageError
from abstract_domain_model.models import SummaryAdded
from abstract_domain_model.transform import from_dict
from readmodel.state_manager.database import Database
from readmodel.state_manager.event_handler import EventHandler
from readmodel.errors import UnknownEventError
from readmodel.errors import DuplicateEventError
from readmodel.state_manager.schema import Base
from readmodel.state_manager.schema import Citation
from readmodel.state_manager.schema import TagInstance
from readmodel.state_manager.schema import Tag
from readmodel.state_manager.schema import Time
from readmodel.state_manager.schema import Person
from readmodel.state_manager.schema import Place
from readmodel.state_manager.schema import Name
from readmodel.state_manager.schema import Summary


class Config:
    """minimal class for setting up an in memory db for this test"""

    def __init__(self):
        self.DB_URI = "sqlite+pysqlite:///:memory:"
        self.DEBUG = False


@pytest.fixture
def db():
    c = Config()
    # stm timeout is an asyncio.sleep value: by setting it to 0 we defer control
    # back to the main thread but return to it as soon as possible.
    db = Database(c, stm_timeout=0)
    db.check_database_init()
    return db


@pytest.fixture
def handler(db):
    return EventHandler(database_instance=db)


@pytest.fixture
def handle_event(handler):
    return handler.handle_event


@pytest.fixture
def basic_meta():
    return {
        "transaction_id": str(uuid4()),
        "app_version": "0.0.0",
        "user_id": "testy-tester",
        "timestamp": str(datetime.utcnow()),
    }


@pytest.fixture
def meta_id():
    return "de71f08f-022e-4f50-a0a0-8b86838e19be"


@pytest.fixture
def citation_guid():
    return str(uuid4())


@pytest.fixture
def summary_guid():
    return str(uuid4())


@pytest.fixture
def place_guid():
    return str(uuid4())


@pytest.fixture
def summary_args(summary_guid, citation_guid):
    return {
        "id": summary_guid,
        "citation_id": citation_guid,
        "text": "some random text here please!",
    }


@pytest.fixture
def citation_args(citation_guid, summary_guid, meta_id):
    return {
        "summary_id": summary_guid,
        "id": citation_guid,
        "text": "some nice text",
        "meta_id": meta_id,
    }


@pytest.fixture
def person_args(summary_guid, citation_guid):
    return {
        "summary_id": summary_guid,
        "citation_id": citation_guid,
        "id": str(uuid4()),
        "name": "Charlemagne",
        "citation_start": 4,
        "citation_end": 10,
    }


@pytest.fixture
def place_args_with_coords(summary_guid, place_guid, citation_guid):
    return {
        "summary_id": summary_guid,
        "citation_id": citation_guid,
        "id": place_guid,
        "name": "Charlemagne",
        "citation_start": 4,
        "citation_end": 10,
        "longitude": 1.9235,
        "latitude": 7.2346,
        "geo_shape": "{some long geoshape file in geojson format}",
    }


@pytest.fixture
def place_args(summary_guid, place_guid, citation_guid):
    return {
        "summary_id": summary_guid,
        "citation_id": citation_guid,
        "id": place_guid,
        "name": "Charlemagne",
        "citation_start": 4,
        "citation_end": 10,
    }


@pytest.fixture
def time_args(summary_guid, citation_guid):
    return {
        "summary_id": summary_guid,
        "citation_id": citation_guid,
        "id": str(uuid4()),
        "name": "1847:3:8:18",
        "citation_start": 4,
        "citation_end": 10,
    }


@pytest.fixture
def meta_args(citation_guid, meta_id):
    return {
        "citation_id": citation_guid,
        "id": meta_id,
        "title": "A Scholarly Book",
        "author": "Samwise",
        "publisher": "Dragon Press",
        "kwargs": {},
    }


@pytest.fixture
def meta_args_with_arbitrary_fields(citation_guid):
    return {
        "citation_id": citation_guid,
        "id": str(uuid4()),
        "title": "A Scholarly Book",
        "author": "Samwise",
        "publisher": "Dragon Press",
        "kwargs": {
            "unexpected": "but still shows up",
            "also didnt plan for this": "but should come through anyways",
        },
    }


@pytest.fixture
def SUMMARY_ADDED(basic_meta, summary_args):
    return {"type": "SUMMARY_ADDED", **basic_meta, "payload": {**summary_args}}


@pytest.fixture
def CITATION_ADDED(basic_meta, citation_args):
    return {"type": "CITATION_ADDED", **basic_meta, "payload": {**citation_args}}


@pytest.fixture
def PERSON_ADDED(basic_meta, person_args):
    return {"type": "PERSON_ADDED", **basic_meta, "payload": {**person_args}}


@pytest.fixture
def PERSON_TAGGED(basic_meta, person_args):
    return {"type": "PERSON_TAGGED", **basic_meta, "payload": {**person_args}}


@pytest.fixture
def PLACE_ADDED(basic_meta, place_args_with_coords):
    return {"type": "PLACE_ADDED", **basic_meta, "payload": {**place_args_with_coords}}


@pytest.fixture
def PLACE_TAGGED(basic_meta, place_args):
    return {"type": "PLACE_TAGGED", **basic_meta, "payload": {**place_args}}


@pytest.fixture
def TIME_ADDED(basic_meta, time_args):
    return {"type": "TIME_ADDED", **basic_meta, "payload": {**time_args}}


@pytest.fixture
def TIME_TAGGED(basic_meta, time_args):
    return {"type": "TIME_TAGGED", **basic_meta, "payload": {**time_args}}


@pytest.fixture
def META_ADDED_basic(basic_meta, meta_args):
    return {"type": "META_ADDED", **basic_meta, "payload": {**meta_args}}


@pytest.fixture
def META_ADDED_more(basic_meta, meta_args_with_arbitrary_fields):
    return {
        "type": "META_ADDED",
        **basic_meta,
        "payload": {**meta_args_with_arbitrary_fields},
    }


def test_unknown_event_raises_error(handle_event):
    with pytest.raises(UnknownMessageError):
        handle_event({"type": "this doesnt exist", "event_id": 1})


@pytest.mark.asyncio
async def test_citation_added(db, handle_event, CITATION_ADDED, SUMMARY_ADDED):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, SUMMARY_ADDED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(CITATION_ADDED)
    payload = CITATION_ADDED["payload"]
    with Session(db._engine, future=True) as sess:
        citation_guid = payload["id"]
        text = payload["text"]
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.guid == citation_guid
        assert res.text == text


@pytest.mark.asyncio
async def test_person_added(db, handle_event, SUMMARY_ADDED, PERSON_ADDED):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, PERSON_ADDED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(PERSON_ADDED)
    payload = PERSON_ADDED["payload"]
    names = payload["name"]
    person_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        assert res.guid == person_guid
        assert res.names == names


@pytest.mark.asyncio
async def test_person_tagged(
    db, handle_event, SUMMARY_ADDED, PERSON_ADDED, PERSON_TAGGED
):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, PERSON_ADDED, PERSON_TAGGED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(PERSON_ADDED)
    handle_event(PERSON_TAGGED)
    payload = PERSON_ADDED["payload"]
    names = payload["name"]
    person_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        assert res.guid == person_guid
        assert res.names == names
        person_id = res.id

        # confirm that we've created two Tag Instances
        tags = sess.execute(
            select(TagInstance).where(TagInstance.tag_id == person_id)
        ).scalars()
        c = 0
        for tag in tags:
            c += 1
        assert c == 2


@pytest.mark.asyncio
async def test_place_added(db, handle_event, SUMMARY_ADDED, PLACE_ADDED):
    # for i, event in enumerate([SUMMARY_ADDED, PLACE_ADDED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(PLACE_ADDED)
    payload = PLACE_ADDED["payload"]
    names = payload["name"]
    place_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        assert res.guid == place_guid
        assert res.names == names


@pytest.mark.asyncio
async def test_place_tagged(db, handle_event, SUMMARY_ADDED, PLACE_ADDED, PLACE_TAGGED):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, PLACE_ADDED, PLACE_TAGGED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(PLACE_ADDED)
    handle_event(PLACE_TAGGED)
    payload = PLACE_ADDED["payload"]
    names = payload["name"]
    latitude = payload["latitude"]
    longitude = payload["longitude"]
    geoshape = payload["geo_shape"]
    place_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        assert res.guid == place_guid
        assert res.names == names
        assert res.latitude == latitude
        assert res.longitude == longitude
        assert res.geoshape == geoshape
        place_id = res.id

        # confirm that we've created two Tag Instances
        tags = sess.execute(
            select(TagInstance).where(TagInstance.tag_id == place_id)
        ).scalars()
        c = 0
        for tag in tags:
            c += 1
        assert c == 2


@pytest.mark.asyncio
async def test_time_added(db, handle_event, SUMMARY_ADDED, TIME_ADDED):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, TIME_ADDED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(TIME_ADDED)
    payload = TIME_ADDED["payload"]
    name = payload["name"]
    time_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        assert res.guid == time_guid
        assert res.name == name


@pytest.mark.asyncio
async def test_time_tagged(db, handle_event, SUMMARY_ADDED, TIME_ADDED, TIME_TAGGED):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, TIME_ADDED, TIME_TAGGED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(TIME_ADDED)
    handle_event(TIME_TAGGED)
    payload = TIME_ADDED["payload"]
    name = payload["name"]
    time_guid = payload["id"]
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        assert res.guid == time_guid
        assert res.name == name
        time_id = res.id

        # confirm that we've created two Tag Instances
        tags = sess.execute(
            select(TagInstance).where(TagInstance.tag_id == time_id)
        ).scalars()
        c = 0
        for tag in tags:
            c += 1
        assert c == 2


@pytest.mark.asyncio
async def test_meta_added_basic(
    db, handle_event, SUMMARY_ADDED, CITATION_ADDED, META_ADDED_basic
):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, CITATION_ADDED, META_ADDED_basic]):
    #     event["event_id"] = i + 1
    citation_guid = CITATION_ADDED["payload"]["id"]
    meta = dict(**META_ADDED_basic["payload"])

    del meta["citation_id"]
    del meta["id"]
    meta_string = json.dumps(meta)
    handle_event(SUMMARY_ADDED)
    handle_event(CITATION_ADDED)
    # make sure meta is starts empty
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == None
    handle_event(META_ADDED_basic)
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == meta_string


@pytest.mark.asyncio
async def test_meta_added_more(
    db, handle_event, SUMMARY_ADDED, CITATION_ADDED, META_ADDED_more
):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, CITATION_ADDED, META_ADDED_more]):
    #     event["event_id"] = i + 1
    citation_guid = CITATION_ADDED["payload"]["id"]
    meta = dict(**META_ADDED_more["payload"])

    del meta["citation_id"]
    del meta["id"]
    meta_string = json.dumps(meta)
    handle_event(SUMMARY_ADDED)
    handle_event(CITATION_ADDED)
    # make sure meta is starts empty
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == None
    handle_event(META_ADDED_more)
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == meta_string


@pytest.mark.skip("Need to rebuild logic to avoid duplicates.")
@pytest.mark.asyncio
async def test_reject_event_with_duplicate_id(
    db, handle_event, SUMMARY_ADDED, CITATION_ADDED
):
    # ensure each event_id is unique to prevent duplicate_event errors
    # for i, event in enumerate([SUMMARY_ADDED, CITATION_ADDED]):
    #     event["event_id"] = i + 1
    handle_event(SUMMARY_ADDED)
    handle_event(CITATION_ADDED)
    with pytest.raises(DuplicateEventError):
        handle_event(CITATION_ADDED)
