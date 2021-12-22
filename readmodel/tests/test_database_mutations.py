import asyncio
import json
import pytest
import random
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state_manager.database import Database

from app.state_manager.schema import Base
from app.state_manager.schema import Citation
from app.state_manager.schema import TagInstance
from app.state_manager.schema import Tag
from app.state_manager.schema import Time
from app.state_manager.schema import Person
from app.state_manager.schema import Place
from app.state_manager.schema import Name
from app.state_manager.schema import Summary


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
    return Database(c, stm_timeout=0)


@pytest.fixture
def summary_data_1():
    guid = str(uuid4())
    text = "a summary text of who, where when"
    return guid, text


@pytest.fixture
def summary_data_2():
    guid = str(uuid4())
    text = "another summary text of who, where when"
    return guid, text


@pytest.fixture
def citation_data_1():
    guid = str(uuid4())
    text = "A sample text to test"
    return guid, text


@pytest.fixture
def citation_data_2():
    guid = str(uuid4())
    text = "Some further sample text to test"
    return guid, text


@pytest.fixture
def summary_guid():
    return str(uuid4())


@pytest.fixture
def person_guid():
    return str(uuid4())


@pytest.fixture
def place_guid():
    return str(uuid4())


@pytest.fixture
def time_guid():
    return str(uuid4())


@pytest.fixture
def citation_guid():
    return str(uuid4())


@pytest.fixture
def start_char():
    return 1


@pytest.fixture
def stop_char():
    return 5


@pytest.fixture
def person_name_1():
    return "Frederick"


@pytest.fixture
def person_name_2():
    return "Frederick the Great"


@pytest.fixture
def place_name_1():
    return "Constantinople"


@pytest.fixture
def place_name_2():
    return "Istanbul"


@pytest.fixture
def time_name():
    return "1824:3:9:31"


@pytest.fixture
def coords():
    return 4.5345, 9.2347


@pytest.fixture
def geoshape():
    return "{type: a shape, some more info, and all in geojson format}"


@pytest.fixture
def meta_data_min():
    return {
        "author": "Søren Aabye Kierkegaard",
        "publisher": "University of Copenhagen",
        "title": "Sickness unto Death",
    }


@pytest.fixture
def meta_data_more():
    return {
        "author": "Søren Aabye Kierkegaard",
        "publisher": "University of Copenhagen",
        "title": "Sickness unto Death",
        "extra field 1": "who knows",
        "extra field 2": "so much fun!",
    }


@pytest.fixture
def was_called():
    hit = [False]

    def outer(func):
        def inner(*args, **kwargs):
            nonlocal hit
            hit[0] = True
            func(*args, **kwargs)

        return inner

    return hit, outer


def test_database_exists(db):
    assert db != None


@pytest.mark.asyncio
async def test_create_summary(db, summary_data_1):
    ...


@pytest.mark.asyncio
async def test_create_citation(db, citation_data_1, summary_guid):
    assert len(db._Database__short_term_memory.keys()) == 0
    # seed database with a root summary
    db.create_summary(summary_guid=summary_guid, text="this is irrelevant")
    citation_guid, text = citation_data_1
    db.create_citation(
        summary_guid=summary_guid, citation_guid=citation_guid, text=text
    )
    assert len(db._Database__short_term_memory.keys()) == 1

    # double check that citation has made it into the database
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.text == text
        assert res.guid == citation_guid

    # check that short term memory is cleared
    await asyncio.sleep(0.000001)
    assert len(db._Database__short_term_memory.keys()) == 0


# test person


@pytest.mark.asyncio
async def test_handle_person_update_new_no_cache(
    db,
    summary_guid,
    was_called,
    person_guid,
    start_char,
    stop_char,
    person_name_1,
    monkeypatch,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # seed the db with a summary
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))

    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid=person_guid,
        person_name=person_name_1,
        start_char=start_char,
        stop_char=stop_char,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        # check our person details
        assert res.names == person_name_1
        assert res.guid == person_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_person_update_existing_no_cache(
    db,
    summary_guid,
    person_guid,
    start_char,
    stop_char,
    person_name_1,
    person_name_2,
    was_called,
    monkeypatch,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # seed the db with a summary and a person
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))

        sess.add(Person(guid=person_guid, names=person_name_1))

    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid=person_guid,
        person_name=person_name_2,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        # check our person details
        assert res.names == person_name_1 + "|" + person_name_2
        assert res.guid == person_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_person_update_new_and_cache(
    db,
    summary_guid,
    person_guid,
    start_char,
    stop_char,
    person_name_1,
    person_name_2,
    was_called,
    monkeypatch,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid=person_guid,
        person_name=person_name_1,
        start_char=start_char,
        stop_char=stop_char,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        # check our person details
        assert res.names == person_name_1
        assert res.guid == person_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_person_update_existing_and_cache(
    db,
    summary_guid,
    person_guid,
    start_char,
    stop_char,
    person_name_1,
    person_name_2,
    was_called,
    monkeypatch,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Person(guid=person_guid, names=person_name_1))
    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid=person_guid,
        person_name=person_name_2,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(
            select(Person).where(Person.guid == person_guid)
        ).scalar_one()
        # check our person details
        assert res.names == person_name_1 + "|" + person_name_2
        assert res.guid == person_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


# test place


@pytest.mark.asyncio
async def test_handle_place_update_new_no_cache(
    db,
    summary_guid,
    was_called,
    place_guid,
    start_char,
    stop_char,
    place_name_1,
    coords,
    geoshape,
    monkeypatch,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # seed the db with a summary
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))
    lat, long = coords

    db.handle_place_update(
        summary_guid=summary_guid,
        place_guid=place_guid,
        place_name=place_name_1,
        start_char=start_char,
        stop_char=stop_char,
        latitude=lat,
        longitude=long,
        geoshape=geoshape,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        # check our place details
        assert res.names == place_name_1
        assert res.guid == place_guid
        assert res.latitude == lat
        assert res.longitude == long
        assert res.geoshape == geoshape
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_place_update_existing_no_cache(
    db,
    summary_guid,
    place_guid,
    start_char,
    stop_char,
    place_name_1,
    place_name_2,
    was_called,
    monkeypatch,
    coords,
    geoshape,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False
    lat, long = coords
    # seed the db with a citation and a place
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))

        sess.add(
            Place(
                guid=place_guid,
                names=place_name_1,
                latitude=lat,
                longitude=long,
                geoshape=geoshape,
            )
        )

    db.handle_place_update(
        summary_guid=summary_guid,
        place_guid=place_guid,
        place_name=place_name_2,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        # check our place details
        assert res.names == place_name_1 + "|" + place_name_2
        assert res.guid == place_guid
        assert res.latitude == lat
        assert res.longitude == long
        assert res.geoshape == geoshape
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_place_update_new_and_cache(
    db,
    summary_guid,
    place_guid,
    start_char,
    stop_char,
    place_name_1,
    was_called,
    monkeypatch,
    coords,
    geoshape,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    lat, long = coords
    db.handle_place_update(
        summary_guid=summary_guid,
        place_guid=place_guid,
        place_name=place_name_1,
        start_char=start_char,
        stop_char=stop_char,
        latitude=lat,
        longitude=long,
        geoshape=geoshape,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        # check our place details
        assert res.names == place_name_1
        assert res.guid == place_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_place_update_existing_and_cache(
    db,
    summary_guid,
    place_guid,
    start_char,
    stop_char,
    place_name_1,
    place_name_2,
    was_called,
    monkeypatch,
    coords,
    geoshape,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    lat, long = coords
    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(
            Place(
                guid=place_guid,
                names=place_name_1,
                latitude=lat,
                longitude=long,
                geoshape=geoshape,
            )
        )
    db.handle_place_update(
        summary_guid=summary_guid,
        place_guid=place_guid,
        place_name=place_name_2,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Place).where(Place.guid == place_guid)).scalar_one()
        # check our place details
        assert res.names == place_name_1 + "|" + place_name_2
        assert res.guid == place_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


# test time


@pytest.mark.asyncio
async def test_handle_time_update_new_no_cache(
    db,
    summary_guid,
    was_called,
    time_guid,
    start_char,
    stop_char,
    time_name,
    monkeypatch,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # seed the db with a summary
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))

    db.handle_time_update(
        summary_guid=summary_guid,
        time_guid=time_guid,
        time_name=time_name,
        start_char=start_char,
        stop_char=stop_char,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        # check our time details
        assert res.name == time_name
        assert res.guid == time_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_time_update_existing_no_cache(
    db,
    summary_guid,
    time_guid,
    start_char,
    stop_char,
    time_name,
    was_called,
    monkeypatch,
):
    # UPDATE 6.14.21: cache is now always checked

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # seed the db with a summary and a time
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Summary(guid=summary_guid, text="not important"))

        sess.add(Time(guid=time_guid, name=time_name))

    db.handle_time_update(
        summary_guid=summary_guid,
        time_guid=time_guid,
        time_name=time_name,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        # check our time details
        assert res.name == time_name
        assert res.guid == time_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_time_update_new_and_cache(
    db,
    summary_guid,
    time_guid,
    start_char,
    stop_char,
    time_name,
    was_called,
    monkeypatch,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    db.handle_time_update(
        summary_guid=summary_guid,
        time_guid=time_guid,
        time_name=time_name,
        start_char=start_char,
        stop_char=stop_char,
        is_new=True,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        # check our time details
        assert res.name == time_name
        assert res.guid == time_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


@pytest.mark.asyncio
async def test_handle_time_update_existing_and_cache(
    db,
    summary_guid,
    time_guid,
    start_char,
    stop_char,
    time_name,
    was_called,
    monkeypatch,
):

    # set up cache hit checker
    called, wrapper = was_called
    wrapped_func = wrapper(db.add_to_stm)
    monkeypatch.setattr(db, "add_to_stm", wrapped_func)
    assert called[0] == False

    # this time use create summary to cache summary_guid
    db.create_summary(summary_guid=summary_guid, text="not important")
    assert len(db._Database__short_term_memory.keys()) == 1
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(Time(guid=time_guid, name=time_name))
    db.handle_time_update(
        summary_guid=summary_guid,
        time_guid=time_guid,
        time_name=time_name,
        start_char=start_char,
        stop_char=stop_char,
        is_new=False,
    )

    with Session(db._engine, future=True) as sess, sess.begin():
        res = sess.execute(select(Time).where(Time.guid == time_guid)).scalar_one()
        # check our time details
        assert res.name == time_name
        assert res.guid == time_guid
        # check our tag instance details
        assert len(res.tag_instances) == 1
        assert res.tag_instances[0].start_char == 1
        assert res.tag_instances[0].stop_char == 5
        # check that the tag links to the summary created earlier
        assert res.tag_instances[0].summary.guid == summary_guid

    # check if cache was hit
    assert called[0] == True


# test meta
@pytest.mark.asyncio
async def test_add_meta_to_citation_no_extra_args(
    db, citation_data_1, summary_guid, meta_data_min
):
    citation_guid, text = citation_data_1
    db.create_summary(summary_guid=summary_guid, text="this is irrelevant")
    db.create_citation(
        summary_guid=summary_guid, citation_guid=citation_guid, text=text
    )

    db.add_meta_to_citation(citation_guid=citation_guid, **meta_data_min)

    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == json.dumps(meta_data_min)


@pytest.mark.asyncio
async def test_add_meta_to_citation_with_extra_args(
    db, citation_data_1, summary_guid, meta_data_more
):
    db.create_summary(summary_guid=summary_guid, text="this is irrelevant")
    citation_guid, text = citation_data_1
    db.create_citation(
        summary_guid=summary_guid, citation_guid=citation_guid, text=text
    )

    db.add_meta_to_citation(citation_guid=citation_guid, **meta_data_more)

    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert res.meta == json.dumps(meta_data_more)


@pytest.mark.asyncio
async def test_handle_name_only_new(db, citation_data_1, summary_guid):
    db.create_summary(summary_guid=summary_guid, text="this is irrelevant")
    citation_guid, text = citation_data_1
    db.create_citation(
        summary_guid=summary_guid, citation_guid=citation_guid, text=text
    )
    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid="test-guid-1",
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    db.handle_place_update(
        summary_guid=summary_guid,
        place_guid="test-guid-2",
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        latitude=random.random(),
        longitude=random.random(),
        is_new=True,
    )
    db.handle_time_update(
        summary_guid=summary_guid,
        time_guid="test-guid-3",
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    with Session(db._engine, future=True) as session:
        names = ["test-name-1", "test-name-2", "test-name-3"]
        guids = ["test-guid-1", "test-guid-2", "test-guid-3"]
        for name, guid in zip(names, guids):
            res = session.execute(select(Name).where(Name.name == name)).scalar_one()
            assert res != None
            assert guid in res.guids


@pytest.mark.asyncio
async def test_handle_name_with_repeats(db, citation_data_1, citation_data_2):
    summary_guid_1 = str(uuid4())
    summary_guid_2 = str(uuid4())
    _, text = citation_data_1
    db.create_summary(summary_guid=summary_guid_1, text=text)
    db.handle_person_update(
        summary_guid=summary_guid_1,
        person_guid="test-guid-1",
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    db.handle_place_update(
        summary_guid=summary_guid_1,
        place_guid="test-guid-2",
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        latitude=random.random(),
        longitude=random.random(),
        is_new=True,
    )
    db.handle_time_update(
        summary_guid=summary_guid_1,
        time_guid="test-guid-3",
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )

    # add a second citation
    _, text_2 = citation_data_2
    db.create_summary(summary_guid=summary_guid_2, text=text_2)
    db.handle_person_update(
        summary_guid=summary_guid_2,
        person_guid="test-guid-4",
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    db.handle_place_update(
        summary_guid=summary_guid_2,
        place_guid="test-guid-5",
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        latitude=random.random(),
        longitude=random.random(),
        is_new=True,
    )
    db.handle_time_update(
        summary_guid=summary_guid_2,
        time_guid="test-guid-6",
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    with Session(db._engine, future=True) as session:
        names = ["test-name-1", "test-name-2", "test-name-3"]
        guids = [
            ("test-guid-1", "test-guid-4"),
            ("test-guid-2", "test-guid-5"),
            ("test-guid-3", "test-guid-6"),
        ]
        for name, (guid1, guid2) in zip(names, guids):

            res = session.execute(select(Name).where(Name.name == name)).scalar_one()
            assert res != None
            assert guid1 in res.guids
            assert guid2 in res.guids

        # double check that there are no extra names floating around
        res = session.execute(select(Name)).scalars()
        res_list = [r.name for r in res]
        assert len(res_list) == 3


@pytest.mark.asyncio
async def test_handle_name_doesnt_duplicate_guids(db, citation_data_1, summary_guid):
    citation_guid, text = citation_data_1
    db.create_summary(summary_guid=summary_guid, text=text)
    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid="test-guid-1",
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    # now add exactly the same name and GUID
    db.handle_person_update(
        summary_guid=summary_guid,
        person_guid="test-guid-1",
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=False,
    )
    with Session(db._engine, future=True) as session:
        res = session.execute(select(Name)).scalars()
        res_list = [r for r in res]
        assert len(res_list) == 1
        name = res_list[0]
        assert len(name.guids) == 1
