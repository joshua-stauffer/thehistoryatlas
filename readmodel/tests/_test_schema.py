import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text

from app.state_manager.schema import Base, Citation, TimeTag, PersonTag, PlaceTag

@pytest.fixture
def engine():
    engine = create_engine('sqlite+pysqlite:///:memory:',
                            echo=True,
                            future=True)
    Base.metadata.create_all(engine)
    return engine

def test_db_exists(engine):
    assert engine != None

def test_citation_to_timetag_relationship(engine):
    test_text = 'Something Happened'
    test_time = 'November 1931'
    
    timetag = TimeTag(name=test_time)
    citation = Citation(
        text=test_text,
        meta='someone said this',
        timetag=timetag)

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([timetag, citation])

        assert timetag.citations[0].text == test_text
        assert citation.timetag.name == test_time

def test_persontag_to_timetag_relationship(engine):
    test_name = 'Giovanni Girolamo Kapsberger'
    test_time = '1637'
    
    timetag = TimeTag(name=test_time)
    person = PersonTag(
        names=test_name,
        timetag=timetag)

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([timetag, person])

        assert timetag.people[0].names == test_name
        assert person.timetag.name == test_time


def test_placetag_to_timetag_relationship(engine):
    test_name = 'Paris'
    test_time = '1200'
    
    timetag = TimeTag(name=test_time)
    place = PlaceTag(
        names=test_name,
        longitude=1.5345,
        latitude=1.35345,
        shape='geojson shape string here of arbitrary length',
        timetag=timetag)

    with Session(engine, future=True) as sess, sess.begin():
        sess.add_all([timetag, place])

        assert timetag.places[0].names == test_name
        assert place.timetag.name == test_time
