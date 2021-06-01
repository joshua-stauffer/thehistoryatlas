import asyncio
import json
import logging
import pytest
import random
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state_manager.database import Database
from app.state_manager.schema import (Citation, TagInstance, Time, Person,
                                      Place, Name)

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

# constants
TYPE_ENUM = set(['PERSON', 'PLACE', 'TIME'])
DB_COUNT = 100
FUZZ_ITERATIONS = 10

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
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
    citations = list()
    people = list()
    places = list()
    times = list()
    cit_guids = list()
    person_guids = list()
    place_guids = list()
    time_guids = list()
    names = list()
    for _ in range(DB_COUNT//2):
        person_guid = str(uuid4())
        person_guids.append(person_guid)
        person_name = f'A Person Name {_}'
        people.append(Person(
            guid=person_guid,
            names=person_name))
        place_guid = str(uuid4())
        place_guids.append(place_guid)
        place_name = f'A Place Name {_}'
        places.append(Place(
            guid=place_guid,
            names=place_name,
            latitude=random.random(),
            longitude=random.random(),
            geoshape='A geoshape string {_}' if random.random() > 0.7 else None))
        time_guid = str(uuid4())
        time_guids.append(time_guid)
        time_name = f'A Time Name {_}'
        times.append(Time(
            guid=time_guid,
            name=time_name))
        # add names to list
        names.extend([person_name, place_name, time_name])
    entities = [(person, place, time) 
                for person, place, time in zip(people, places, times)]
    for n in range(DB_COUNT):
        guid = f'fake-guid-{n}'
        cit_guids.append(guid)
        person, place, time = entities[n % len(entities)]
        citations.append(Citation(
            guid=guid,
            text=f'test text {n}',
            meta=json.dumps({'some': 'meta data'}),
            time_tag=time.name,
            tags=[
                TagInstance(
                    start_char=random.randint(0,100),
                    stop_char=random.randint(100, 200),
                    tag=entity)
                for entity in (person, place, time)
            ]))

    with Session(_db._engine, future=True) as session:
        session.add_all([*citations, *people, *places, *times])
        # manually update names
        for person in people:
            _db._handle_name(person.names, person.guid, session)
        for place in places:
            _db._handle_name(place.names, place.guid, session)
        for time in times:
            _db._handle_name(time.name, time.guid, session)
        session.commit()
    db_dict = {
        'citation_guids': cit_guids,
        'person_guids': person_guids,
        'place_guids': place_guids,
        'time_guids': time_guids,
        'names': names
    }
    return _db, db_dict
    
def load_db(db_tuple):
    db, db_dict = db_tuple
    assert db != None

# test that database preconditions are valid

def test_each_citation_has_tags(db_tuple):
    db, db_dict = db_tuple
    citation_guids = db_dict['citation_guids']
    with Session(db._engine, future=True) as session:
        for guid in citation_guids:
            res = session.execute(
                select(Citation).where(Citation.guid == guid)
            ).scalar_one()
            assert len(res.tags) > 0

def test_each_person_has_tags(db_tuple):
    db, db_dict = db_tuple
    person_guids = db_dict['person_guids']
    with Session(db._engine, future=True) as session:
        for guid in person_guids:
            res = session.execute(
                select(Person).where(Person.guid == guid)
            ).scalar_one()
            assert len(res.tag_instances) > 0

def test_each_place_has_tags(db_tuple):
    db, db_dict = db_tuple
    place_guids = db_dict['place_guids']
    with Session(db._engine, future=True) as session:
        for guid in place_guids:
            res = session.execute(
                select(Place).where(Place.guid == guid)
            ).scalar_one()
            assert len(res.tag_instances) > 0

def test_each_time_has_tags(db_tuple):
    db, db_dict = db_tuple
    time_guids = db_dict['time_guids']
    with Session(db._engine, future=True) as session:
        for guid in time_guids:
            res = session.execute(
                select(Time).where(Time.guid == guid)
            ).scalar_one()
            assert len(res.tag_instances) > 0

def test_each_citation_has_a_timetag(db_tuple):
    db, db_dict = db_tuple
    citation_guids = db_dict['citation_guids']
    with Session(db._engine, future=True) as session:
        for guid in citation_guids:
            res = session.execute(
                select(Citation).where(Citation.guid==guid)
            ).scalar_one()
            assert any(t.tag.type=='TIME' for t in res.tags)

def test_all_citations_have_timetag_cache(db_tuple):
    db, db_dict = db_tuple
    citation_guids = db_dict['citation_guids']
    with Session(db._engine, future=True) as session:
        for guid in citation_guids:
            res = session.execute(
                select(Citation).where(Citation.guid==guid)
            ).scalar_one()
            assert isinstance(res.time_tag, str)

# test sad path

def test_get_citations_returns_error_with_unknown_guid(db_tuple):
    db, db_dict = db_tuple
    guid = str(uuid4())
    res = db.get_citations([guid])
    assert len(res) == 0

def test_get_manifest_by_person_returns_empty_list(db_tuple):
    db, db_dict = db_tuple
    res = db.get_manifest_by_person('Definitely Not a Person')
    assert isinstance(res, list)
    assert len(res) == 0
# test successful queries

def test_get_citation_fuzz_test(db_tuple):
    db, db_dict = db_tuple
    citation_guids = db_dict['citation_guids']
    # ensure that there are no duplicates in citation_guids
    test = set(citation_guids)
    assert len(test) == len(citation_guids)
    # fuzz
    # NOTE: this slows down the test considerably at higher iterations
    for _ in range(FUZZ_ITERATIONS):
        c = citation_guids[:]
        guids = list()
        log.info(f'Loop {_}')
        # draw guids to get
        count = random.randint(1, DB_COUNT)
        for _ in range(count):
            guids.append(c.pop(random.randint(0, len(c)-1)))
        log.info(f'Count: {count}')
        log.info(f'GUIDs head: {guids[:10]}')
        res = db.get_citations(guids)
        assert isinstance(res, list)
        assert len(res) == len(guids)
        for cit in res:
            assert cit['guid'] in guids
            # describe the shape of expected properties
            assert isinstance(cit, dict)
            assert cit['text'] != None
            assert isinstance(cit['text'], str)
            assert isinstance(cit['meta'], dict)
            assert isinstance(cit['tags'], list)
            for t in cit['tags']:
                assert isinstance(t, dict)
                assert isinstance(t['start_char'], int)
                assert isinstance(t['stop_char'], int)
                assert t['tag_type'] in TYPE_ENUM
                if t['tag_type'] == 'TIME':
                    assert isinstance(t['name'], str)
                elif t['tag_type'] == 'PERSON':
                    assert isinstance(t['names'], list)
                else:
                    assert isinstance(t['names'], list)
                    assert isinstance(t['coords'], dict)
                    assert isinstance(t['coords']['longitude'], float)
                    assert isinstance(t['coords']['latitude'], float)
                    if g := t['coords'].get('geoshape'):
                        assert isinstance(g, str)

def test_get_manifest_by_person(db_tuple):
    db, db_dict = db_tuple
    person_guids = db_dict['person_guids']
    for guid in person_guids:
        res = db.get_manifest_by_person(guid)
        assert isinstance(res, list)
        assert all(isinstance(e, str) for e in res)
        assert len(res) > 0

def test_get_manifest_by_place(db_tuple):
    db, db_dict = db_tuple
    place_guids = db_dict['place_guids']
    for guid in place_guids:
        res = db.get_manifest_by_place(guid)
        assert isinstance(res, list)
        assert all(isinstance(e, str) for e in res)
        assert len(res) > 0


def test_get_manifest_by_time(db_tuple):
    db, db_dict = db_tuple
    time_guids = db_dict['time_guids']
    for guid in time_guids:
        res = db.get_manifest_by_time(guid)
        assert isinstance(res, list)
        assert all(isinstance(e, str) for e in res)
        assert len(res) > 0

def test_get_guids_by_name(db_tuple):
    db, db_dict = db_tuple
    names = db_dict['names']
    guids = [*db_dict['person_guids'], *db_dict['place_guids'], *db_dict['time_guids']]
    for name in names:
        res = db.get_guids_by_name(name)
        assert len(res) == 1


def test_get_guids_by_name_returns_empty(db_tuple):
    db, db_dict = db_tuple
    res = db.get_guids_by_name('This name doesnt exist')
    assert isinstance(res, list)
    assert len(res) == 0

def test_tag_instances(db_tuple):
    db, db_dict = db_tuple
    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(TagInstance)
            ).scalars()
        count = [1 for _ in res]
        assert len(count) == 300

def test_get_entity_summary_by_guid_batch_returns_empty(db_tuple):
    db, db_dict = db_tuple
    res = db.get_entity_summary_by_guid_batch([])
    assert isinstance(res, list)
    assert len(res) == 0

def test_get_entity_summary_by_guid_batch(db_tuple):
    db, db_dict = db_tuple
    time_guids = db_dict['time_guids'][:10]
    place_guids = db_dict['place_guids'][:10]
    person_guids = db_dict['person_guids'][:10]
    combined_guids = [*time_guids, *place_guids, *person_guids]
    assert len(combined_guids) == 30
    res = db.get_entity_summary_by_guid_batch(combined_guids)
    assert isinstance(res, list)
    assert len(res) == 30
    for summary in res:
        assert isinstance(summary, dict)
        guid = summary['guid']
        assert isinstance(guid, str)
        if summary['type'] == 'TIME':
            assert guid in time_guids
        elif summary['type'] == 'PLACE':
            assert guid in place_guids
        elif summary['type'] == 'PERSON':
            assert guid in person_guids
        else:
            assert False # Summary type had an unexpected value
        assert summary['citation_count'] > 0
        assert isinstance(summary['names'], list)
        for name in summary['names']:
            assert isinstance(name, str)
        assert isinstance(summary['first_citation_date'], str)
        assert isinstance(summary['last_citation_date'], str)
        assert summary['first_citation_date'] <= summary['last_citation_date']