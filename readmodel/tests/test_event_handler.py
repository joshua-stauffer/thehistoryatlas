import asyncio
from datetime import datetime
import json
import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state_manager.database import Database
from app.state_manager.event_handler import EventHandler
from app.state_manager.errors import UnknownEventError
from app.state_manager.schema import Citation, TagInstance, Time, Person, Place

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
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
        'transaction_guid': str(uuid4()),
        'app_version': '0.0.0',
        'user': 'testy-tester',
        'timestamp': str(datetime.utcnow()),
        'event_id': 1
    }

@pytest.fixture
def citation_guid():
    return str(uuid4())

@pytest.fixture
def place_guid():
    return str(uuid4())

@pytest.fixture
def citation_args(citation_guid):
    return {
        'citation_guid': citation_guid,
        'text': 'some nice text',
        'tags': ['a-guid', 'b-guid', 'c-guid'],
        'meta': 'meta data guid'
    }

@pytest.fixture
def person_args(citation_guid):
    return {
        'citation_guid': citation_guid,
        'person_guid': str(uuid4()),
        'person_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def place_args_with_coords(citation_guid, place_guid):
    return {
        'citation_guid': citation_guid,
        'place_guid': place_guid,
        'place_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10,
        'longitude': 1.9235,
        'latitude': 7.2346,
        'geoshape': '{some long geoshape file in geojson format}'
    }

@pytest.fixture
def place_args(citation_guid, place_guid):
    return {
        'citation_guid': citation_guid,
        'place_guid': place_guid,
        'place_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def time_args(citation_guid):
    return {
        'citation_guid': citation_guid,
        'time_guid': str(uuid4()),
        'time_name': '1847:3:8:18',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def meta_args(citation_guid):
    return {
        'citation_guid': citation_guid,
        'meta_guid': str(uuid4()),
        'title': 'A Scholarly Book',
        'author': 'Samwise',
        'publisher': 'Dragon Press'
    }

@pytest.fixture
def meta_args_with_arbitrary_fields(citation_guid):
    return {
        'citation_guid': citation_guid,
        'meta_guid': str(uuid4()),
        'title': 'A Scholarly Book',
        'author': 'Samwise',
        'publisher': 'Dragon Press',
        'unexpected': 'but still shows up',
        'also didnt plan for this': 'but should come through anyways'
    }

@pytest.fixture
def CITATION_ADDED(basic_meta, citation_args):
    return {
        'type': 'CITATION_ADDED',
        **basic_meta,
        'payload': {
            **citation_args
        }
    }

@pytest.fixture
def PERSON_ADDED(basic_meta, person_args):
    return {
        'type': 'PERSON_ADDED',
        **basic_meta,
        'payload': {
            **person_args
        }
    }

@pytest.fixture
def PERSON_TAGGED(basic_meta, person_args):
    return {
        'type': 'PERSON_TAGGED',
        **basic_meta,
        'payload': {
            **person_args
        }
    }

@pytest.fixture
def PLACE_ADDED(basic_meta, place_args_with_coords):
    return {
        'type': 'PLACE_ADDED',
        **basic_meta,
        'payload': {
            **place_args_with_coords
        }
    }

@pytest.fixture
def PLACE_TAGGED(basic_meta, place_args):
    return {
        'type': 'PLACE_TAGGED',
        **basic_meta,
        'payload': {
            **place_args
        }
    }

@pytest.fixture
def TIME_ADDED(basic_meta, time_args):
    return {
        'type': 'TIME_ADDED',
        **basic_meta,
        'payload': {
            **time_args
        }
    }

@pytest.fixture
def TIME_TAGGED(basic_meta, time_args):
    return {
        'type': 'TIME_TAGGED',
        **basic_meta,
        'payload': {
            **time_args
        }
    }

@pytest.fixture
def META_ADDED_basic(basic_meta, meta_args):
    return {
        'type': 'META_ADDED',
        **basic_meta,
        'payload': {
            **meta_args
        }
    }

@pytest.fixture
def META_ADDED_more(basic_meta, meta_args_with_arbitrary_fields):
    return {
        'type': 'META_ADDED',
        **basic_meta,
        'payload': {
            **meta_args_with_arbitrary_fields
        }
    }

def test_unknown_event_raises_error(handle_event):
    with pytest.raises(UnknownEventError):
        handle_event({
            'type': 'this doesnt exist'
        })

@pytest.mark.asyncio
async def test_citation_added(db, handle_event, CITATION_ADDED):
    handle_event(CITATION_ADDED)
    payload = CITATION_ADDED['payload']
    with Session(db._engine, future=True) as sess:
        citation_guid = payload['citation_guid']
        text = payload['text']
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.guid == citation_guid
        assert res.text == text

@pytest.mark.asyncio
async def test_person_added(db, handle_event, CITATION_ADDED, PERSON_ADDED):
    handle_event(CITATION_ADDED)
    handle_event(PERSON_ADDED)
    payload = PERSON_ADDED['payload']
    names = payload['person_name']
    person_guid = payload['person_guid']
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        assert res.guid == person_guid
        assert res.names == names


@pytest.mark.asyncio
async def test_person_tagged(db, handle_event, CITATION_ADDED, PERSON_ADDED,
    PERSON_TAGGED):
    handle_event(CITATION_ADDED)
    handle_event(PERSON_ADDED)
    handle_event(PERSON_TAGGED)
    payload = PERSON_ADDED['payload']
    names = payload['person_name']
    person_guid = payload['person_guid']
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
async def test_place_added(db, handle_event, CITATION_ADDED, PLACE_ADDED):
    handle_event(CITATION_ADDED)
    handle_event(PLACE_ADDED)
    payload = PLACE_ADDED['payload']
    names = payload['place_name']
    place_guid = payload['place_guid']
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Place).where(Place.guid == place_guid)
        ).scalar_one()
        assert res.guid == place_guid
        assert res.names == names

@pytest.mark.asyncio
async def test_place_tagged(db, handle_event, CITATION_ADDED, PLACE_ADDED,
    PLACE_TAGGED):
    handle_event(CITATION_ADDED)
    handle_event(PLACE_ADDED)
    handle_event(PLACE_TAGGED)
    payload = PLACE_ADDED['payload']
    names = payload['place_name']
    latitude = payload['latitude']
    longitude = payload['longitude']
    geoshape = payload['geoshape']
    place_guid = payload['place_guid']
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Place).where(Place.guid == place_guid)
        ).scalar_one()
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
async def test_time_added(db, handle_event, CITATION_ADDED, TIME_ADDED):
    handle_event(CITATION_ADDED)
    handle_event(TIME_ADDED)
    payload = TIME_ADDED['payload']
    name = payload['time_name']
    time_guid = payload['time_guid']
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Time).where(Time.guid == time_guid)
        ).scalar_one()
        assert res.guid == time_guid
        assert res.name == name


@pytest.mark.asyncio
async def test_time_tagged(db, handle_event, CITATION_ADDED, TIME_ADDED,
    TIME_TAGGED):
    handle_event(CITATION_ADDED)
    handle_event(TIME_ADDED)
    handle_event(TIME_TAGGED)
    payload = TIME_ADDED['payload']
    name = payload['time_name']
    time_guid = payload['time_guid']
    with Session(db._engine, future=True) as sess:

        res = sess.execute(
            select(Time).where(Time.guid == time_guid)
        ).scalar_one()
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
async def test_meta_added_basic(db, handle_event, CITATION_ADDED, META_ADDED_basic):
    citation_guid = CITATION_ADDED['payload']['citation_guid']
    meta = dict(**META_ADDED_basic['payload'])

    del meta['citation_guid']
    del meta['meta_guid']
    meta_string = json.dumps(meta)

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
async def test_meta_added_more(db, handle_event, CITATION_ADDED,
    META_ADDED_more):
    citation_guid = CITATION_ADDED['payload']['citation_guid']
    meta = dict(**META_ADDED_more['payload'])

    del meta['citation_guid']
    del meta['meta_guid']
    meta_string = json.dumps(meta)

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
