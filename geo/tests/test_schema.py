from datetime import datetime
from random import random
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import pytest
from app.schema import Place
from app.schema import Name
from app.schema import UpdateTracker
from app.schema import Base

@pytest.fixture
def engine():
    URL = 'sqlite+pysqlite:///:memory:'
    engine = create_engine(
        URL,
        echo=False,
        future=True)
    Base.metadata.create_all(engine)
    return engine

def test_name(engine):
    with Session(engine, future=True) as session:
        somename = 'filippo'
        someone = Name(name=somename)
        session.add(someone)
        session.commit()
        res = session.execute(
            select(Name).where(Name.id==1)
        ).scalar_one()
        assert res.name == somename

def test_place(engine):
    with Session(engine, future=True) as session:
        lat = random()
        long = random()
        shape = '{"some": ["geojson", "shape"]}'
        somewhere = Place(
            latitude=lat,
            longitude=long,
            geoshape=shape
        )
        session.add(somewhere)
        session.commit()
        res = session.execute(
            select(Place).where(Place.id==1)
        ).scalar_one()
        assert res.latitude == lat
        assert res.longitude == long
        assert res.geoshape == shape


def test_association(engine):
    name1 = 'Kalmthout'
    name2 = 'Calmpthout'
    lat1 = random()
    long1 = random()
    lat2 = random()
    long2 = random()
    with Session(engine, future=True) as session:
        place1 = Place(
            latitude=lat1,
            longitude=long1)
        place2 = Place(
            latitude=lat2,
            longitude=long2)
        name1 = Name(
            name=name1,
            places=[place1, place2])
        name2  = Name(
            name=name2,
            places=[place1, place2])
        session.add_all([place1, place2, name1, name2])
        session.commit()

        place_query_1 = session.execute(
            select(Place).where(Place.id == 1)
        ).scalar_one()
        assert all([name in [name1, name2]
                    for name in place_query_1.names])

        place_query_2 = session.execute(
            select(Place).where(Place.id == 2)
        ).scalar_one()
        assert all([name in [name1, name2]
                    for name in place_query_2.names])

        coords = [(lat1, long1), (lat2, long2)]

        name_query_1 = session.execute(
            select(Name).where(Name.id == 1)
        ).scalar_one()
        assert all([(place.latitude, place.longitude) in coords
                    for place in name_query_1.places])

        name_query_2 = session.execute(
            select(Name).where(Name.id == 1)
        ).scalar_one()
        assert all([(place.latitude, place.longitude) in coords
                    for place in name_query_2.places])

def test_update_tracker(engine):
    time = str(datetime.utcnow())
    with Session(engine, future=True) as session:
        update = UpdateTracker(
            timestamp=time)
        session.add(update)
        session.commit()
        res = session.execute(
            select(UpdateTracker).where(UpdateTracker.id == 1)
        ).scalar_one()
        assert res.timestamp == time

def test_name_duplicates_raise_error(engine):
    name1 = 'Kalmthout'
    name2 = 'Kalmthout'
    with Session(engine, future=True) as session:
        name1 = Name(
            name=name1)
        name2  = Name(
            name=name2)
        session.add_all([name1, name2])
        with pytest.raises(IntegrityError):
            session.commit()

def test_name_uniqueness_capitalization_matters(engine):
    name1 = 'Kalmthout'
    name2 = 'kalmthout'
    with Session(engine, future=True) as session:
        name1 = Name(
            name=name1)
        name2  = Name(
            name=name2)
        session.add_all([name1, name2])
        session.commit() # doesn't throw an error