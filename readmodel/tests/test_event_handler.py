import asyncio
from copy import deepcopy
from datetime import datetime
from dataclasses import replace, dataclass
import json
import pytest
from uuid import uuid4
import random
from sqlalchemy import select
from sqlalchemy.orm import Session

from abstract_domain_model.errors import UnknownMessageError
from abstract_domain_model.models import (
    SummaryAdded,
    SummaryAddedPayload,
    CitationAdded,
    CitationAddedPayload,
    PersonAdded,
    PersonAddedPayload,
    PersonTagged,
    PersonTaggedPayload,
    PlaceAdded,
    PlaceAddedPayload,
    PlaceTagged,
    PlaceTaggedPayload,
    TimeAdded,
    TimeAddedPayload,
    TimeTagged,
    TimeTaggedPayload,
    MetaAdded,
    MetaAddedPayload,
)
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


@pytest.fixture
def handler(db):
    return EventHandler(database_instance=db)


@pytest.fixture
def handle_event(handler):
    return handler.handle_event


@pytest.fixture
def basic_meta():
    return {
        "transaction_id": "70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        "app_version": "0.0.0",
        "user_id": "testy-tester",
        "timestamp": "2022-12-18 21:20:41.262212",
    }


@pytest.fixture
def meta_id():
    return "de71f08f-022e-4f50-a0a0-8b86838e19be"


@pytest.fixture
def citation_guid():
    return "f8e39a88-5220-41f4-b9f0-8880255f84be"


@pytest.fixture
def summary_guid():
    return "1fb8ee2e-177b-4e2b-8cc2-14335fb2f867"


@pytest.fixture
def place_guid():
    return "3c35e5f3-8788-41de-a052-d9de8410da17"


@pytest.fixture
def time_guid():
    return "a3bddcb6-d03e-4770-81cb-27799c410558"


@pytest.fixture
def summary_args(summary_guid, citation_guid):
    return {
        "id": summary_guid,
        "citation_id": citation_guid,
        "text": "some random text here please!",
        "index": 1,
    }


@pytest.fixture
def citation_args(citation_guid, summary_guid, meta_id):
    return {
        "summary_id": summary_guid,
        "id": citation_guid,
        "text": "some nice text",
        "meta_id": meta_id,
        "index": 2,
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
        "index": 3,
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
        "index": 4,
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
        "index": 5,
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
        "index": 6,
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
        "index": 7,
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
        "index": 8,
    }


@pytest.fixture
def SUMMARY_ADDED(summary_guid, citation_guid):
    return SummaryAdded(
        type="SUMMARY_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=1,
        payload=SummaryAddedPayload(
            id=summary_guid,
            citation_id=citation_guid,
            text="some random text here please!",
        ),
    )


@pytest.fixture
def CITATION_ADDED(summary_guid, citation_guid, meta_id):
    return CitationAdded(
        type="CITATION_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=2,
        payload=CitationAddedPayload(
            summary_id=summary_guid,
            id=citation_guid,
            text="some nice text",
            meta_id=meta_id,
        ),
    )


@pytest.fixture
def PERSON_ADDED(summary_guid, citation_guid):
    return PersonAdded(
        type="PERSON_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=3,
        payload=PersonAddedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id="65052229-69ab-4827-a5f5-39a4bc1a2ada",
            name="Charlemagne",
            citation_start=4,
            citation_end=10,
        ),
    )


@pytest.fixture
def PERSON_TAGGED(summary_guid, citation_guid):
    return PersonTagged(
        type="PERSON_TAGGED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=4,
        payload=PersonTaggedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id="65052229-69ab-4827-a5f5-39a4bc1a2ada",
            name="Charlemagne",
            citation_start=4,
            citation_end=10,
        ),
    )


@pytest.fixture
def PLACE_ADDED(summary_guid, citation_guid, place_guid):
    return PlaceAdded(
        type="PLACE_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=5,
        payload=PlaceAddedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id=place_guid,
            name="Charlemagne",
            citation_start=4,
            citation_end=10,
            longitude=1.9235,
            latitude=7.2346,
            geo_shape="{some long geoshape file in geojson format}",
        ),
    )


@pytest.fixture
def PLACE_TAGGED(summary_guid, citation_guid, place_guid):
    return PlaceTagged(
        type="PLACE_TAGGED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=6,
        payload=PlaceTaggedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id=place_guid,
            name="Charlemagne",
            citation_start=4,
            citation_end=10,
        ),
    )


@pytest.fixture
def TIME_ADDED(time_guid, summary_guid, citation_guid):
    return TimeAdded(
        type="TIME_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=7,
        payload=TimeAddedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id=time_guid,
            name="1847:3:8:18",
            citation_start=4,
            citation_end=10,
        ),
    )


@pytest.fixture
def TIME_TAGGED(summary_guid, citation_guid, time_guid):
    return TimeTagged(
        type="TIME_TAGGED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=8,
        payload=TimeTaggedPayload(
            summary_id=summary_guid,
            citation_id=citation_guid,
            id=time_guid,
            name="1847:3:8:18",
            citation_start=4,
            citation_end=10,
        ),
    )


@pytest.fixture
def META_ADDED_basic(citation_guid, meta_id):
    return MetaAdded(
        type="META_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=9,
        payload=MetaAddedPayload(
            id=meta_id,
            citation_id=citation_guid,
            title="A Scholarly Book",
            author="Samwise",
            publisher="Dragon Press",
            kwargs={},
        ),
    )


@pytest.fixture
def META_ADDED_more(meta_id, citation_guid):
    return MetaAdded(
        type="META_ADDED",
        transaction_id="70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        app_version="0.0.0",
        user_id="testy-tester",
        timestamp="2022-12-18 21:20:41.262212",
        index=10,
        payload=MetaAddedPayload(
            id=meta_id,
            citation_id=citation_guid,
            title="A Scholarly Book",
            author="Samwise",
            publisher="Dragon Press",
            kwargs={
                "unexpected": "but still shows up",
                "also didnt plan for this": "but should come through anyways",
            },
        ),
    )


def test_unknown_event_raises_error(handle_event):
    @dataclass
    class NotAnEvent:
        type: str
        index: int

    with pytest.raises(UnknownEventError):
        handle_event(NotAnEvent(type="NotAnEvent", index=0))


@pytest.mark.asyncio
async def test_citation_added(db, handle_event, CITATION_ADDED, SUMMARY_ADDED):
    handle_event(SUMMARY_ADDED)
    handle_event(CITATION_ADDED)
    payload = CITATION_ADDED.payload
    with Session(db._engine, future=True) as sess:
        citation_guid = payload.id
        text = payload.text
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.guid == citation_guid
        assert res.text == text


@pytest.mark.asyncio
async def test_person_added(db, handle_event, SUMMARY_ADDED, PERSON_ADDED):
    handle_event(SUMMARY_ADDED)
    handle_event(PERSON_ADDED)
    payload = PERSON_ADDED.payload
    names = payload.name
    person_guid = payload.id
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
    handle_event(SUMMARY_ADDED)
    handle_event(PERSON_ADDED)
    handle_event(PERSON_TAGGED)
    payload = PERSON_ADDED.payload
    names = payload.name
    person_guid = payload.id
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
    handle_event(SUMMARY_ADDED)
    handle_event(PLACE_ADDED)
    payload = PLACE_ADDED.payload
    names = payload.name
    place_guid = payload.id
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        assert res.guid == place_guid
        assert res.names == names


@pytest.mark.asyncio
async def test_place_tagged(db, handle_event, SUMMARY_ADDED, PLACE_ADDED, PLACE_TAGGED):
    handle_event(SUMMARY_ADDED)
    handle_event(PLACE_ADDED)
    handle_event(PLACE_TAGGED)
    payload = PLACE_ADDED.payload
    names = payload.name
    latitude = payload.latitude
    longitude = payload.longitude
    geoshape = payload.geo_shape
    place_guid = payload.id
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
    handle_event(SUMMARY_ADDED)
    handle_event(TIME_ADDED)
    payload = TIME_ADDED.payload
    name = payload.name
    time_guid = payload.id
    with Session(db._engine, future=True) as sess:

        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        assert res.guid == time_guid
        assert res.name == name


@pytest.mark.asyncio
async def test_time_tagged(db, handle_event, SUMMARY_ADDED, TIME_ADDED, TIME_TAGGED):
    handle_event(SUMMARY_ADDED)
    handle_event(TIME_ADDED)
    handle_event(TIME_TAGGED)
    payload = TIME_ADDED.payload
    name = payload.name
    time_guid = payload.id
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
async def test_reject_event_with_duplicate_id(
    db, handle_event, SUMMARY_ADDED, CITATION_ADDED
):
    # ensure each event_id is unique to prevent duplicate_event errors
    summary_dict = replace(SUMMARY_ADDED, index=1)
    citation_dict_1 = replace(CITATION_ADDED, index=2)
    citation_dict_2 = replace(CITATION_ADDED, index=2)
    handle_event(summary_dict)
    handle_event(citation_dict_1)
    with pytest.raises(DuplicateEventError):
        handle_event(citation_dict_2)
