from datetime import datetime
import pytest
from uuid import uuid4
from app.state_manager.event_composer import EventComposer

@pytest.fixture
def composer(basic_meta):
    return EventComposer(**basic_meta)

@pytest.fixture
def basic_meta():
    return {
        'transaction_guid': str(uuid4()),
        'app_version': '0.0.0',
        'user': 'testy-tester',
        'timestamp': str(datetime.utcnow())
    }

@pytest.fixture
def citation_args():
    return {
        'citation_guid': str(uuid4()),
        'text': 'some nice text',
        'tags': ['a-guid', 'b-guid', 'c-guid'],
        'meta': 'meta data guid'
    }

@pytest.fixture
def person_args():
    return {
        'citation_guid': str(uuid4()),
        'person_guid': str(uuid4()),
        'person_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def place_args_with_coords():
    return {
        'citation_guid': str(uuid4()),
        'place_guid': str(uuid4()),
        'place_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10,
        'longitude': 1.9235,
        'latitude': 7.2346,
        'geoshape': 'some geoshape file'
    }

@pytest.fixture
def place_args():
    return {
        'citation_guid': str(uuid4()),
        'place_guid': str(uuid4()),
        'place_name': 'Charlemagne',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def time_args():
    return {
        'citation_guid': str(uuid4()),
        'time_guid': str(uuid4()),
        'time_name': '1847:3:8:18',
        'citation_start': 4,
        'citation_end': 10
    }

@pytest.fixture
def meta_args():
    return {
        'citation_guid': str(uuid4()),
        'meta_guid': str(uuid4()),
        'title': 'A Scholarly Book',
        'author': 'Samwise',
        'publisher': 'Dragon Press'
    }

@pytest.fixture
def meta_args_with_arbitrary_fields():
    return {
        'citation_guid': str(uuid4()),
        'meta_guid': str(uuid4()),
        'title': 'A Scholarly Book',
        'author': 'Samwise',
        'publisher': 'Dragon Press',
        'unexpected': 'but still shows up',
        'also didnt plan for this': 'but should come through anyways'
    }

def test_basic_meta(composer, basic_meta):
    assert composer._EventComposer__meta == basic_meta

def test_make_CITATION_ADDED(composer, basic_meta, citation_args):
    assert len(composer.events) == 0
    composer.make_CITATION_ADDED(**citation_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'CITATION_ADDED',
        'payload': citation_args
    }

def test_make_PERSON_ADDED(composer, basic_meta, person_args):
    assert len(composer.events) == 0
    composer.make_PERSON_ADDED(**person_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'PERSON_ADDED',
        'payload': person_args
    }

def test_make_PLACE_ADDED(composer, basic_meta, place_args_with_coords):
    assert len(composer.events) == 0
    composer.make_PLACE_ADDED(**place_args_with_coords)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'PLACE_ADDED',
        'payload': place_args_with_coords
    }

def test_make_TIME_ADDED(composer, basic_meta, time_args):
    assert len(composer.events) == 0
    composer.make_TIME_ADDED(**time_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'TIME_ADDED',
        'payload': time_args
    }

def test_make_PERSON_TAGGED(composer, basic_meta, person_args):
    assert len(composer.events) == 0
    composer.make_PERSON_TAGGED(**person_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'PERSON_TAGGED',
        'payload': person_args
    }

def test_make_PLACE_TAGGED(composer, basic_meta, place_args):
    assert len(composer.events) == 0
    composer.make_PLACE_TAGGED(**place_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'PLACE_TAGGED',
        'payload': place_args
    }

def test_make_TIME_TAGGED(composer, basic_meta, time_args):
    assert len(composer.events) == 0
    composer.make_TIME_TAGGED(**time_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'TIME_TAGGED',
        'payload': time_args
    }

def test_make_META_ADDED(composer, basic_meta, meta_args):
    assert len(composer.events) == 0
    composer.make_META_ADDED(**meta_args)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'META_ADDED',
        'payload': meta_args
    }

def test_make_META_ADDED_with_arbitrary_fields(
    composer, basic_meta, meta_args_with_arbitrary_fields):
    assert len(composer.events) == 0
    composer.make_META_ADDED(**meta_args_with_arbitrary_fields)
    assert len(composer.events) == 1
    e = composer.events[0]
    assert e == {
        **basic_meta,
        'type': 'META_ADDED',
        'payload': meta_args_with_arbitrary_fields
    }

def test_composer_maintains_order(composer, person_args,
    place_args, time_args, meta_args):
    assert len(composer.events) == 0
    composer.make_PERSON_ADDED(**person_args)
    composer.make_PLACE_TAGGED(**place_args)
    composer.make_META_ADDED(**meta_args)
    composer.make_TIME_TAGGED(**time_args)
    assert len(composer.events) == 4
    e = composer.events
    assert e[0]['type'] == 'PERSON_ADDED'
    assert e[1]['type'] == 'PLACE_TAGGED'
    assert e[2]['type'] == 'META_ADDED'
    assert e[3]['type'] == 'TIME_TAGGED'

def test_composer_orders_citation_first(composer, person_args,
    place_args, time_args, meta_args, citation_args):
    assert len(composer.events) == 0
    composer.make_PERSON_ADDED(**person_args)
    composer.make_PLACE_TAGGED(**place_args)
    composer.make_META_ADDED(**meta_args)
    composer.make_TIME_TAGGED(**time_args)
    composer.make_CITATION_ADDED(**citation_args)
    assert len(composer.events) == 5
    e = composer.events
    assert e[0]['type'] == 'CITATION_ADDED'
    assert e[1]['type'] == 'PERSON_ADDED'
    assert e[2]['type'] == 'PLACE_TAGGED'
    assert e[3]['type'] == 'META_ADDED'
    assert e[4]['type'] == 'TIME_TAGGED'
