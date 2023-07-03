import asyncio
import pytest
import random
from uuid import uuid4, UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from the_history_atlas.apps.readmodel.schema import Source
from the_history_atlas.apps.readmodel.schema import Citation
from the_history_atlas.apps.readmodel.schema import Time
from the_history_atlas.apps.readmodel.schema import Person
from the_history_atlas.apps.readmodel.schema import Place
from the_history_atlas.apps.readmodel.schema import Name
from the_history_atlas.apps.readmodel.schema import Summary


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
        "pub_date": "1/1/1",
        "id": "53c499d4-4ac1-4f48-a978-e7abf263d5e9",
    }


@pytest.fixture
def meta_data_more():
    return {
        "author": "Søren Aabye Kierkegaard",
        "publisher": "University of Copenhagen",
        "title": "Sickness unto Death",
        "extra field 1": "who knows",
        "extra field 2": "so much fun!",
        "pub_date": "1/1/1",
        "id": "63ff66d2-1145-4b6c-9113-d4db93f6fff2",
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


@pytest.mark.asyncio
async def test_add_meta_to_citation_no_extra_args(
    readmodel_db, citation_data_1, summary_guid, meta_data_min, engine
):
    citation_guid, text = citation_data_1
    readmodel_db.create_summary(id=summary_guid, text="this is irrelevant")
    readmodel_db.create_citation(id=citation_guid, summary_id=summary_guid, text=text)

    readmodel_db.create_source(citation_id=citation_guid, **meta_data_min)

    with Session(engine, future=True) as sess:
        citation = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert citation.source.author == meta_data_min["author"]
        assert citation.source.publisher == meta_data_min["publisher"]
        assert citation.source.title == meta_data_min["title"]


@pytest.mark.asyncio
async def test_add_meta_to_citation_with_extra_args(
    readmodel_db, citation_data_1, summary_guid, meta_data_more, engine
):
    readmodel_db.create_summary(id=summary_guid, text="this is irrelevant")
    citation_guid, text = citation_data_1
    readmodel_db.create_citation(id=citation_guid, summary_id=summary_guid, text=text)

    readmodel_db.create_source(citation_id=citation_guid, **meta_data_more)

    with Session(engine, future=True) as sess:
        citation = sess.execute(
            select(Citation).where(Citation.guid == citation_guid)
        ).scalar_one()
        assert citation.source.author == meta_data_more["author"]
        assert citation.source.publisher == meta_data_more["publisher"]
        assert citation.source.title == meta_data_more["title"]


@pytest.mark.asyncio
async def test_handle_name_only_new(
    readmodel_db, citation_data_1, summary_guid, engine
):
    readmodel_db.create_summary(id=summary_guid, text="this is irrelevant")
    citation_guid, text = citation_data_1
    readmodel_db.create_citation(id=citation_guid, summary_id=summary_guid, text=text)
    readmodel_db.handle_person_update(
        person_id="test-guid-1",
        summary_id=summary_guid,
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    readmodel_db.handle_place_update(
        place_id="test-guid-2",
        summary_id=summary_guid,
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        is_new=True,
        latitude=random.random(),
        longitude=random.random(),
    )
    readmodel_db.handle_time_update(
        time_id="test-guid-3",
        summary_id=summary_guid,
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    with Session(engine, future=True) as session:
        names = ["test-name-1", "test-name-2", "test-name-3"]
        guids = ["test-guid-1", "test-guid-2", "test-guid-3"]
        for name, guid in zip(names, guids):
            res = session.execute(select(Name).where(Name.name == name)).scalar_one()
            assert res != None
            assert guid in res.guids


@pytest.mark.asyncio
async def test_handle_name_with_repeats(
    readmodel_db, citation_data_1, citation_data_2, engine
):
    summary_guid_1 = str(uuid4())
    summary_guid_2 = str(uuid4())
    _, text = citation_data_1
    readmodel_db.create_summary(id=summary_guid_1, text=text)
    readmodel_db.handle_person_update(
        person_id="test-guid-1",
        summary_id=summary_guid_1,
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    readmodel_db.handle_place_update(
        place_id="test-guid-2",
        summary_id=summary_guid_1,
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        is_new=True,
        latitude=random.random(),
        longitude=random.random(),
    )
    readmodel_db.handle_time_update(
        time_id="test-guid-3",
        summary_id=summary_guid_1,
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )

    # add a second citation
    _, text_2 = citation_data_2
    readmodel_db.create_summary(id=summary_guid_2, text=text_2)
    readmodel_db.handle_person_update(
        person_id="test-guid-4",
        summary_id=summary_guid_2,
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    readmodel_db.handle_place_update(
        place_id="test-guid-5",
        summary_id=summary_guid_2,
        place_name="test-name-2",
        start_char=1,
        stop_char=5,
        is_new=True,
        latitude=random.random(),
        longitude=random.random(),
    )
    readmodel_db.handle_time_update(
        time_id="test-guid-6",
        summary_id=summary_guid_2,
        time_name="test-name-3",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    with Session(engine, future=True) as session:
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
async def test_handle_name_doesnt_duplicate_guids(
    readmodel_db, citation_data_1, summary_guid, engine
):
    citation_guid, text = citation_data_1
    readmodel_db.create_summary(id=summary_guid, text=text)
    readmodel_db.handle_person_update(
        person_id="test-guid-1",
        summary_id=summary_guid,
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=True,
    )
    # now add exactly the same name and GUID
    readmodel_db.handle_person_update(
        person_id="test-guid-1",
        summary_id=summary_guid,
        person_name="test-name-1",
        start_char=1,
        stop_char=5,
        is_new=False,
    )
    with Session(engine, future=True) as session:
        res = session.execute(select(Name)).scalars()
        res_list = [r for r in res]
        assert len(res_list) == 1
        name = res_list[0]
        assert len(name.guids) == 1


def test_create_source_with_citation_relationship(readmodel_db, engine):
    source_id = "cd71d777-f8e6-4b82-bdca-96ef47dcaeb7"
    citation_id = "c4bd0c8e-801f-46d2-b876-c23c3fd9ce15"
    title = "new source"
    author = "new author"
    publisher = "publisher name"
    pub_date = "1/1/2023"

    citation = Citation(
        guid=citation_id,
    )
    with Session(engine, future=True) as session:
        session.add(citation)
        session.commit()

    readmodel_db.create_source(
        id=source_id,
        title=title,
        author=author,
        publisher=publisher,
        pub_date=pub_date,
        citation_id=citation_id,
    )
    with Session(engine, future=True) as session:
        source = session.query(Source).where(Source.id == source_id).one()
        assert source.id == source_id
        assert source.title == title
        assert source.author == author
        assert source.publisher == publisher
        assert source.pub_date == pub_date
        assert len(source.citations) == 1
        assert source.citations[0].guid == citation_id


def test_tag_source(readmodel_db, engine):
    source_id = "08ea9177-66e6-4494-b2f3-c8f4f05456a7"
    citation_id = "29a34448-099e-44bc-9bf8-5e4222ccf509"
    title = "another source"
    author = "another author"
    publisher = "another publisher name"
    pub_date = "1/1/2023"

    citation = Citation(
        guid=citation_id,
    )
    source = Source(
        id=source_id,
        title=title,
        author=author,
        publisher=publisher,
        pub_date=pub_date,
    )
    with Session(engine, future=True) as session:
        session.add_all([citation, source])
        session.commit()

    readmodel_db.add_source_to_citation(source_id=source_id, citation_id=citation_id)

    with Session(engine, future=True) as session:
        citation = session.query(Citation).where(Citation.guid == citation_id).one()
        assert citation.source.id == source_id
