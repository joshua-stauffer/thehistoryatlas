import uuid
import pytest
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text

from app.state_manager.schema import (Base, Citation, TagInstance, Tag,
    Time, Person, Place, Name)
from app.state_manager.errors import EmptyNameError

@pytest.fixture
def engine():
    engine = create_engine('sqlite+pysqlite:///:memory:',
                            echo=True,
                            future=True)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def citation_data_1():
    guid = str(uuid4())
    text = 'A sample text to test'
    meta = 'someone said this once'
    return guid, text, meta

@pytest.fixture
def citation_data_2():
    guid = str(uuid4())
    text = 'Some further sample text to test'
    meta = 'someone never said this'
    return guid, text, meta

@pytest.fixture
def tag1():
    return TagInstance(
        start_char=5,
        stop_char=10)

@pytest.fixture
def tag2():
    return TagInstance(
        start_char=8,
        stop_char=12)

@pytest.fixture
def tag3():
    return TagInstance(
        start_char=9,
        stop_char=15)

@pytest.fixture
def tag4():
    return TagInstance(
        start_char=27,
        stop_char=32)

def test_db_exists(engine):
    assert engine != None

def test_citation_and_taginstance(citation_data_1, engine, tag1, tag2):
    """verify relationship between citations and tag instances are correct"""
    guid, text, meta = citation_data_1
    citation = Citation(
        guid=guid,
        text=text,
        meta=meta)
    tag1.citation = citation
    tag2.citation = citation

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([citation, tag1, tag2])

        assert tag1 in citation.tags
        assert tag2 in citation.tags
        assert tag1.citation is citation
        assert tag2.citation is citation

def test_taginstance_and_tag(engine, tag1, tag2):
    """verify relationships between tag instances and tags are correct"""
    tag = Tag(
        guid=str(uuid4()),
        tag_instances=[tag1, tag2]
    )
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([tag, tag1, tag2])
        assert tag1 in tag.tag_instances
        assert tag2 in tag.tag_instances
        assert tag1.tag is tag
        assert tag2.tag is tag

def test_citation_and_tag(engine, citation_data_1, citation_data_2,
    tag1, tag2, tag3, tag4):
    person = Tag(
        guid = str(uuid4()),
        tag_instances = [tag1, tag3]
    )
    place = Tag(
        guid = str(uuid4()),
        tag_instances = [tag2, tag4]
    )
    guid1, text1, meta1 = citation_data_1 
    cit_1 = Citation(
        guid=guid1,
        text=text1,
        meta=meta1,
        tags=[tag1, tag2]
    )
    guid2, text2, meta2 = citation_data_2 
    cit_2 = Citation(
        guid=guid2,
        text=text2,
        meta=meta2,
        tags=[tag3, tag4]
    )

    data = [tag1, tag2, tag3, tag4, cit_1, cit_2, person, place]
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all(data)

        assert person.tag_instances[0].citation is cit_1
        assert place.tag_instances[0].citation is cit_1
        assert person.tag_instances[1].citation is cit_2
        assert place.tag_instances[1].citation is cit_2

def test_tag_inheritance(engine, citation_data_1, citation_data_2):
    time = Time(
        guid = str(uuid4()),
        name = 'November 1963')
    person = Person(
        guid = str(uuid4()),
        names = 'Bach,Johann Sebastian Bach,J.S.Bach')
    place = Place(
        guid=str(uuid4()),
        names='Milan,Milano')
    guid1, text1, meta1 = citation_data_1 
    cit_1 = Citation(
        guid=guid1,
        text=text1,
        meta=meta1)
    guid2, text2, meta2 = citation_data_2 
    cit_2 = Citation(
        guid=guid2,
        text=text2,
        meta=meta2)
    tags = [TagInstance(
        start_char=1,
        stop_char=5,
        citation=c,
        tag=t)
        for t in [time, person, place]
        for c in [cit_1, cit_2]]

    data = [time, person, place, cit_1, cit_2, *tags]
    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all(data)

def test_name_returns_list():
    n = Name(
        name='Ocean',
        guids='some-guid')
    assert isinstance(n.guids, list)
    assert n.guids[0] == 'some-guid'
    print(n.guids)
    assert len(n.guids) == 1

def test_name_on_set():
    n = Name(
        name='Ocean',
        guids='some-guid')
    n.add_guid('Frank')
    assert n.guids[1] == 'Frank'
    assert len(n.guids) == 2

def test_name_on_del():
    n = Name(
        name='Ocean',
        guids='some-guid')
    with pytest.raises(ValueError):
        n.del_guid('Frank')
    assert len(n.guids) == 1
    with pytest.raises(IndexError):
        assert n.guids[1]
    with pytest.raises(EmptyNameError):
        n.del_guid('some-guid')
    n.add_guid('Frank')
    n.del_guid('Frank')
    assert len(n.guids) == 1
