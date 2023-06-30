import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from the_history_atlas.apps.readmodel.schema import Source
from the_history_atlas.apps.readmodel.schema import Citation
from the_history_atlas.apps.readmodel.schema import TagInstance
from the_history_atlas.apps.readmodel.schema import Tag
from the_history_atlas.apps.readmodel.schema import Time
from the_history_atlas.apps.readmodel.schema import Person
from the_history_atlas.apps.readmodel.schema import Place
from the_history_atlas.apps.readmodel.schema import Name
from the_history_atlas.apps.readmodel.schema import Summary
from the_history_atlas.apps.readmodel.schema import EmptyNameError


@pytest.fixture
def summary_data_1():
    guid = str(uuid4())
    text = "A summary of a person doing something somewhere at some time"
    return guid, text


@pytest.fixture
def summary_data_2():
    guid = str(uuid4())
    text = "Another summary of a person doing something somewhere at some time"
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
def tag1():
    return TagInstance(start_char=5, stop_char=10)


@pytest.fixture
def tag2():
    return TagInstance(start_char=8, stop_char=12)


@pytest.fixture
def tag3():
    return TagInstance(start_char=9, stop_char=15)


@pytest.fixture
def tag4():
    return TagInstance(start_char=27, stop_char=32)


def test_db_exists(engine):
    assert engine != None


def test_summary_and_taginstance(summary_data_1, engine, tag1, tag2):
    """verify relationship between summary and tag instances are correct"""
    guid, text = summary_data_1
    summary = Summary(guid=guid, text=text)
    tag1.summary = summary
    tag2.summary = summary

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([summary, tag1, tag2])

        assert tag1 in summary.tags
        assert tag2 in summary.tags
        assert tag1.summary is summary
        assert tag2.summary is summary


def test_summary_and_citation(summary_data_1, citation_data_1, engine):
    """verify relationship between citations and summaries are correct"""
    guid, text = summary_data_1
    guid, text = citation_data_1
    summary = Summary(guid=guid, text=text)
    citation = Citation(guid=guid, text=text)
    summary.citations = [citation]

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([citation, citation])

        assert citation in summary.citations
        assert summary.citations[0] is citation


def test_taginstance_and_tag(engine, tag1, tag2):
    """verify relationships between tag instances and tags are correct"""
    tag = Tag(guid=str(uuid4()), tag_instances=[tag1, tag2])
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([tag, tag1, tag2])
        assert tag1 in tag.tag_instances
        assert tag2 in tag.tag_instances
        assert tag1.tag is tag
        assert tag2.tag is tag


def test_summary_and_tag(
    engine, summary_data_1, summary_data_2, tag1, tag2, tag3, tag4
):
    person = Tag(guid=str(uuid4()), tag_instances=[tag1, tag3])
    place = Tag(guid=str(uuid4()), tag_instances=[tag2, tag4])
    guid1, text1 = summary_data_1
    sum_1 = Summary(guid=guid1, text=text1, tags=[tag1, tag2])
    guid2, text2 = summary_data_2
    sum_2 = Summary(guid=guid2, text=text2, tags=[tag3, tag4])

    data = [tag1, tag2, tag3, tag4, sum_1, sum_2, person, place]
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all(data)

        assert person.tag_instances[0].summary is sum_1
        assert place.tag_instances[0].summary is sum_1
        assert person.tag_instances[1].summary is sum_2
        assert place.tag_instances[1].summary is sum_2


def test_tag_inheritance(engine, summary_data_1, summary_data_2):
    time = Time(guid=str(uuid4()), name="November 1963")
    person = Person(guid=str(uuid4()), names="Bach,Johann Sebastian Bach,J.S.Bach")
    place = Place(guid=str(uuid4()), names="Milan,Milano")
    guid1, text1 = summary_data_1
    sum_1 = Summary(guid=guid1, text=text1)
    guid2, text2 = summary_data_2
    sum_2 = Summary(guid=guid2, text=text2)
    tags = [
        TagInstance(start_char=1, stop_char=5, summary=c, tag=t)
        for t in [time, person, place]
        for c in [sum_1, sum_2]
    ]

    data = [time, person, place, sum_1, sum_2, *tags]
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all(data)


def test_name_returns_list():
    n = Name(name="Ocean", guids="some-guid")
    assert isinstance(n.guids, list)
    assert n.guids[0] == "some-guid"
    print(n.guids)
    assert len(n.guids) == 1


def test_name_on_set():
    n = Name(name="Ocean", guids="some-guid")
    n.add_guid("Frank")
    assert n.guids[1] == "Frank"
    assert len(n.guids) == 2


def test_name_on_del():
    n = Name(name="Ocean", guids="some-guid")
    with pytest.raises(ValueError):
        n.del_guid("Frank")
    assert len(n.guids) == 1
    with pytest.raises(IndexError):
        assert n.guids[1]
    with pytest.raises(EmptyNameError):
        n.del_guid("some-guid")
    n.add_guid("Frank")
    n.del_guid("Frank")
    assert len(n.guids) == 1


def test_create_source(engine):
    source = Source(
        id="cd71d777-f8e6-4b82-bdca-96ef47dcaeb7",
        title="new source",
        author="new author",
        publisher="publisher name",
        pub_date="1/1/2023",
    )
    with Session(engine, future=True) as session:
        session.add(source)
        session.commit()
