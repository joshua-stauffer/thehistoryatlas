import datetime
from random import random
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from geo.geonames import CityRow
from geo.state.database import Database
from geo.state.schema import Name
from geo.state.schema import Place
from geo.state.schema import UpdateTracker

@pytest.fixture
def config():
    class Config:
        def __init__(self):
            self.DB_URI = 'sqlite+pysqlite:///:memory:'
            self.DEBUG = False
    return Config()

@pytest.fixture
def empty_db(config):
    return Database(config)

@pytest.fixture
def result_a():
    return [{'latitude': 1.1,
            'longitude': 2.2},
            {'latitude': 3.3,
            'longitude': 4.4}]

@pytest.fixture
def result_b():
    return [{'latitude': 5.5,
                'longitude': 6.6},
                {'latitude': 7.7,
                'longitude': 8.8}]

@pytest.fixture
def name_a():
    return 'Raul Capablanca'

@pytest.fixture
def name_b():
    return 'Paul Morphy'
    
@pytest.fixture
def db(empty_db, name_a, result_a, name_b, result_b):
    with Session(empty_db._engine, future=True) as session:
        to_commit = list()
        for name, result in zip([name_a, name_b], [result_a, result_b]):

            name1 = Name(name=name)
            to_commit.append(name1)
            for coord_dict in result:
                place = Place(
                    names=[name1],
                    longitude=coord_dict['longitude'],
                    latitude=coord_dict['latitude'])
                to_commit.append(place)
        session.add_all(to_commit)
        session.commit()
    return empty_db

def test_get_coords_by_name_empty_name(db):
    res = db.get_coords_by_name('not a name in the database')
    assert res == []

def test_get_coords_by_name_batch__empty_names(db):
    str_list = ['not', 'a', 'name', 'in', 'the', 'database']
    res = db.get_coords_by_name_batch(str_list)
    for name in str_list:
        assert res[name] == []

def test_get_coords_by_name(db, name_a, result_a):
    lats = [r['latitude'] for r in result_a]
    longs = [r['longitude'] for r in result_a]
    res = db.get_coords_by_name(name_a)
    assert isinstance(res, list)
    for coords in res:
        assert coords['latitude'] in lats
        assert coords['longitude'] in longs

def test_get_coords_by_name_batch(db, name_a, result_a, name_b, result_b):
    lats_a = [r['latitude'] for r in result_a]
    longs_a = [r['longitude'] for r in result_a]
    lats_b = [r['latitude'] for r in result_b]
    longs_b = [r['longitude'] for r in result_b]
    res = db.get_coords_by_name_batch([name_a, name_b])
    assert isinstance(res, dict)
    for coords in res[name_a]:
        assert coords['latitude'] in lats_a
        assert coords['longitude'] in longs_a
    for coords in res[name_b]:
        assert coords['latitude'] in lats_b
        assert coords['longitude'] in longs_b

def test_build_db_ignores_non_cityrow_data(empty_db):
    empty_db.build_db(['This isnt a CityRow'])

def test_build_db_from_city_row(empty_db):
    lat = random()
    long = random()
    geoname_id = 12345
    mod_date = '1111-11-11'
    name = 'abc'
    ascii_name = 'abcd'
    alternate_names = 'a,b,c,d'
    all_names = [name, ascii_name, *alternate_names.split(',')]
    city = CityRow(
        geoname_id=geoname_id,
        latitude=lat,
        longitude=long,
        modification_date=mod_date,
        name=name,
        ascii_name=ascii_name,
        alternate_names=alternate_names)
    empty_db._build_db_from_city_row([city])
    # test that all names are reachable from the place
    with Session(empty_db._engine, future=True) as session:
        place = session.execute(
            select(Place).where(Place.id==1) 
        ).scalar_one()
        # expect only one place
        not_another_place = session.execute(
            select(Place).where(Place.id==2)
        ).scalar_one_or_none()
        assert not_another_place is None
        assert len(place.names) == len(all_names)
        # check that each is unique
        assert len(set(n.name for n in place.names)) == len(all_names)
        for name in all_names:
            name_row = session.execute(
                select(Name).where(Name.name == name)
            ).scalar_one()
            assert name_row.places[0] is place

def test_build_db_update_tracker(empty_db):
    empty_db.build_db(['This isnt a CityRow']) # this triggers an update
    with Session(empty_db._engine, future=True) as session:
        tracker = session.execute(
            select(UpdateTracker).where(UpdateTracker.id == 1)
        ).scalar_one()
        assert isinstance(tracker.timestamp, str)

def test_get_last_update_timestamp(empty_db):
    assert empty_db.get_last_update_timestamp() is None
    empty_db.build_db(['this isnt a CityRow']) # this triggers an update
    assert isinstance(empty_db.get_last_update_timestamp(), datetime.datetime)
