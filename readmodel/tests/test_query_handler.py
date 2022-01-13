import asyncio
import json
import random
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from app.errors import UnknownManifestTypeError, UnknownQueryError
from app.state_manager.database import Database
from app.state_manager.query_handler import QueryHandler
from app.state_manager.schema import (
    Base,
    Citation,
    Name,
    Person,
    Place,
    Summary,
    Tag,
    TagInstance,
    Time,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

# constants
TYPE_ENUM = set(["PERSON", "PLACE", "TIME"])
DB_COUNT = 100
FUZZ_ITERATIONS = 10


class Config:
    """minimal class for setting up an in memory db for this test"""

    def __init__(self):
        self.DB_URI = "sqlite+pysqlite:///:memory:"
        self.DEBUG = False


@pytest.fixture
def _db():
    c = Config()
    # stm timeout is an asyncio.sleep value: by setting it to 0 we defer control
    # back to the main thread but return to it as soon as possible.
    return Database(c, stm_timeout=0)


@pytest.fixture
def db_tuple(_db):
    """
    This fixture manually creates DB_COUNT citations, and DB_COUNT // 2
    of people, places, and times (each). It then associates each citation
    with a person, place, and time, going through the list twice, so that
    each person, place, time is tagged by two different citations.

    NOTE: Because all the db additions are done manually (in order to isolate
    the tests from errors originating in the MUTATION section of the db) the
    addition of names to the Name table is a bit wonky. It's assumed that
    each entity name appears with exactly the same spelling in both citations
    in which it appears.
    """
    summaries = list()
    citations = list()
    people = list()
    places = list()
    times = list()
    cit_guids = list()
    sum_guids = list()
    person_guids = list()
    place_guids = list()
    time_guids = list()
    names = list()
    for _ in range(DB_COUNT // 2):
        person_guid = str(uuid4())
        person_guids.append(person_guid)
        person_name = f"A Person Name {_}"
        people.append(Person(guid=person_guid, names=person_name))
        place_guid = str(uuid4())
        place_guids.append(place_guid)
        place_name = f"A Place Name {_}"
        places.append(
            Place(
                guid=place_guid,
                names=place_name,
                latitude=random.random(),
                longitude=random.random(),
                geoshape="A geoshape string {_}" if random.random() > 0.7 else None,
            )
        )
        time_guid = str(uuid4())
        time_guids.append(time_guid)
        time_name = f"2{_}5{random.randint(0, 9)}|{random.randint(1, 4)}"
        times.append(Time(guid=time_guid, name=time_name))
        # add names to list
        names.extend([person_name, place_name, time_name])
    entities = [
        (person, place, time) for person, place, time in zip(people, places, times)
    ]
    for n in range(DB_COUNT):
        # create a citation
        cit_guid = f"fake-citation-guid-{n}"
        cit_guids.append(cit_guid)
        citation = Citation(
            guid=cit_guid,
            text=f"some citation text {n}",
            meta=json.dumps({"some": "meta data"}),
        )
        citations.append(citation)
        # create a summary
        sum_guid = f"fake-summary-guid-{n}"
        sum_guids.append(sum_guid)
        person, place, time = entities[n % len(entities)]
        summaries.append(
            Summary(
                guid=sum_guid,
                text=f"test text {n}",
                time_tag=time.name,
                tags=[
                    TagInstance(
                        start_char=random.randint(0, 100),
                        stop_char=random.randint(100, 200),
                        tag=entity,
                    )
                    for entity in (person, place, time)
                ],
                citations=[citation],
            )
        )

    with Session(_db._engine, future=True) as session:
        session.add_all([*summaries, *citations, *people, *places, *times])
        # manually update names
        for person in people:
            _db._handle_name(person.names, person.guid, session)
        for place in places:
            _db._handle_name(place.names, place.guid, session)
        for time in times:
            _db._handle_name(time.name, time.guid, session)
        session.commit()
    db_dict = {
        "summary_guids": sum_guids,
        "citation_guids": cit_guids,
        "person_guids": person_guids,
        "place_guids": place_guids,
        "time_guids": time_guids,
        "names": names,
    }
    return _db, db_dict


@pytest.fixture
def handler(db_tuple):
    db, _ = db_tuple
    return QueryHandler(database_instance=db)


@pytest.fixture
def handle_query(handler):
    return handler.handle_query


def test_handle_query_exists(handle_query):
    assert handle_query != None


# sad paths


def test_handle_query_raises_error_on_unknown_type(handle_query):
    with pytest.raises(UnknownQueryError):
        handle_query({"type": "This type doesnt exist"})


def test_get_manifest_raises_error_on_unknown_type(handle_query):
    with pytest.raises(UnknownManifestTypeError):
        handle_query(
            {
                "type": "GET_MANIFEST",
                "payload": {"type": "this type doesnt exist", "guid": "doesnt matter"},
            }
        )


# successful paths


def test_get_citation_by_guid(handle_query, db_tuple):
    _, db_dict = db_tuple
    guids = db_dict["citation_guids"]
    res = handle_query(
        {"type": "GET_CITATION_BY_GUID", "payload": {"citation_guid": guids[1]}}
    )
    assert isinstance(res, dict)
    assert res["type"] == "CITATION_BY_GUID"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["citation"], dict)


def test_get_manifest_person(handle_query, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["person_guids"][0]
    res = handle_query(
        {"type": "GET_MANIFEST", "payload": {"type": "PERSON", "guid": guid}}
    )
    print("manifest is ", res)
    assert isinstance(res, dict)
    assert res["type"] == "MANIFEST"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["guid"], str)
    assert isinstance(res["payload"]["citation_guids"], list)
    assert isinstance(res["payload"]["timeline"], list)
    for r in res["payload"]["timeline"]:
        assert isinstance(r, dict)
        assert isinstance(r["count"], int)
        assert isinstance(r["root_guid"], str)
        assert isinstance(r["year"], int)


def test_get_manifest_place(handle_query, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["place_guids"][0]
    res = handle_query(
        {"type": "GET_MANIFEST", "payload": {"type": "PLACE", "guid": guid}}
    )
    assert isinstance(res, dict)
    assert res["type"] == "MANIFEST"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["guid"], str)
    assert isinstance(res["payload"]["citation_guids"], list)
    assert isinstance(res["payload"]["timeline"], list)
    for r in res["payload"]["timeline"]:
        assert isinstance(r, dict)
        assert isinstance(r["count"], int)
        assert isinstance(r["root_guid"], str)
        assert isinstance(r["year"], int)


def test_get_manifest_time(handle_query, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["time_guids"][0]
    res = handle_query(
        {"type": "GET_MANIFEST", "payload": {"type": "TIME", "guid": guid}}
    )
    assert isinstance(res, dict)
    assert res["type"] == "MANIFEST"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["guid"], str)
    assert isinstance(res["payload"]["citation_guids"], list)
    assert isinstance(res["payload"]["timeline"], list)
    for r in res["payload"]["timeline"]:
        assert isinstance(r, dict)
        assert isinstance(r["count"], int)
        assert isinstance(r["root_guid"], str)
        assert isinstance(r["year"], int)


def test_get_guids_by_name(handle_query, db_tuple):
    _, db_dict = db_tuple
    name = db_dict["names"][0]
    res = handle_query({"type": "GET_GUIDS_BY_NAME", "payload": {"name": name}})
    assert isinstance(res, dict)
    assert res["type"] == "GUIDS_BY_NAME"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["guids"], list)
    assert isinstance(res["payload"]["summaries"], list)


def test_get_fuzzy_search_by_name(handle_query):
    name = "a"
    res = handle_query({"type": "GET_FUZZY_SEARCH_BY_NAME", "payload": {"name": name}})
    assert isinstance(res, dict)
    assert res["type"] == "FUZZY_SEARCH_BY_NAME"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["results"], list)
    assert res["payload"]["name"] == name
    for r in res["payload"]["results"]:
        assert isinstance(r["name"], str)
        assert isinstance(r["guids"], list)
        for id_ in r["guids"]:
            assert isinstance(id_, str)


def test_get_entity_summaries_by_guid_handles_empty_list(handle_query, db_tuple):

    res = handle_query(
        {"type": "GET_ENTITY_SUMMARIES_BY_GUID", "payload": {"guids": []}}
    )
    assert res["type"] == "ENTITY_SUMMARIES_BY_GUID"
    assert isinstance(res["payload"], dict)
    assert len(res["payload"]["results"]) == 0


def test_get_entity_summaries_by_guid_with_invalid_guids(handle_query, db_tuple):
    wrong_guids = [
        "c0c0ba02-b43b-4733-ac09-f35bd06b123f",
        "ee9b40e5-7066-4be6-ac6b-970b79035a22",
        "fbbee7e9-eaa8-4d15-bc0d-46a1ef459343",
    ]

    res = handle_query(
        {"type": "GET_ENTITY_SUMMARIES_BY_GUID", "payload": {"guids": wrong_guids}}
    )

    assert res["type"] == "ENTITY_SUMMARIES_BY_GUID"
    assert isinstance(res["payload"], dict)
    assert len(res["payload"]["results"]) == 0


def test_get_entity_summaries(handle_query, db_tuple):
    _, db_dict = db_tuple

    guids = db_dict["place_guids"][20:25]
    guids.extend(db_dict["time_guids"][20:25])
    guids.extend(db_dict["person_guids"][20:25])

    res = handle_query(
        {"type": "GET_ENTITY_SUMMARIES_BY_GUID", "payload": {"guids": guids}}
    )

    assert res["type"] == "ENTITY_SUMMARIES_BY_GUID"
    assert isinstance(res["payload"], dict)
    assert len(res["payload"]["results"]) == 15

    for entity in res["payload"]["results"]:
        assert entity["type"] in ["PERSON", "PLACE", "TIME"]
        assert UUID(entity["guid"])
        assert isinstance(entity["citation_count"], int)
        assert isinstance(entity["names"], list)
        for name in entity["names"]:
            assert isinstance(name, str)
        assert isinstance(entity["first_citation_date"], str)
        assert isinstance(entity["last_citation_date"], str)


def test_get_place_by_coords_success(handle_query, db_tuple):
    db, db_dict = db_tuple
    # find a set of coordinates to query
    place_guid = db_dict["place_guids"][0]
    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(Place).where(Place.guid == place_guid)
        ).scalar_one()
        latitude = res.latitude
        longitude = res.longitude

    res = handle_query(
        {
            "type": "GET_PLACE_BY_COORDS",
            "payload": {
                "latitude": latitude,
                "longitude": longitude,
            },
        }
    )
    assert res["type"] == "PLACE_BY_COORDS"
    assert res["payload"]["guid"] == place_guid
    assert res["payload"]["latitude"] == latitude
    assert res["payload"]["longitude"] == longitude


def test_get_place_by_coords_failure(handle_query, db_tuple):
    latitude = 1 + random.random()
    longitude = 1 - random.random()
    res = handle_query(
        {
            "type": "GET_PLACE_BY_COORDS",
            "payload": {
                "latitude": latitude,
                "longitude": longitude,
            },
        }
    )
    assert res["type"] == "PLACE_BY_COORDS"
    assert res["payload"]["guid"] == None
    assert res["payload"]["latitude"] == latitude
    assert res["payload"]["longitude"] == longitude
