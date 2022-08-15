from datetime import datetime
import pytest
from uuid import uuid4

from writemodel.state_manager.command_handler import CommandHandler
from writemodel.state_manager.database import Database
from writemodel.state_manager.text_processor import TextHasher
from writemodel.state_manager.handler_errors import (GUIDError, UnknownCommandTypeError,
    CitationMissingFieldsError, CitationExistsError, UnknownTagTypeError)

@pytest.fixture
def hash_text():
    t = TextHasher()
    return t.get_hash

@pytest.fixture
def config():
    class Config:
        """minimal class for setting up an in memory db for this test"""
        def __init__(self):
            self.DB_URI = 'sqlite+pysqlite:///:memory:'
            self.DEBUG = False
    return Config()

@pytest.fixture
def handler(db, hash_text):
    return CommandHandler(
        database_instance=db,
        hash_text=hash_text)

@pytest.fixture
def db(config):
    return Database(config, stm_timeout=0)

@pytest.fixture
def basic_meta():
    return {
        'type': 'PUBLISH_NEW_CITATION',
        'user': 'da schwitz',
        'timestamp': str(datetime.utcnow()),
        'app_version': '0.0.0',
    }

@pytest.fixture
def meta0():
    return {
        'GUID': str(uuid4()),
        'author': 'francesco, natürli',
        'publisher': 'dr papscht',
        'title': 'try this at home'
    }

@pytest.fixture
def citation0(basic_meta, meta0, summary_new):
    return {
        **basic_meta,
        'payload': {
            'GUID': str(uuid4()),
            'text': 'Dr Papscht hett ds Spiez Späck Besteck spät bestellt',
            'tags': [],
            'meta': meta0,
            'summary': summary_new
        }
    }

@pytest.fixture
def meta1():
    return {
        'GUID': str(uuid4()),
        'author': 'francesco, natürli',
        'publisher': 'dr papscht',
        'title': 'try this at home'
    }



@pytest.fixture
def citation1(basic_meta, meta1, summary_existing):
    return {
        **basic_meta,
        'payload': {
            'GUID': str(uuid4()),
            # this text has an extra letter, so is considered unique
            'text': 'Der Papscht hett ds Spiez Späck Besteck spät bestellt',
            'tags': [],
            'meta': meta1,
            'summary': summary_existing
        }
    }

@pytest.fixture
def person_tag_0():
    return {
        'GUID': str(uuid4()),
        'type': 'PERSON',
        'name': 'Papscht',
        'start_char': 3,
        'stop_char': 10
    }

@pytest.fixture
def person_tag_1(person_tag_0):
    return {
        'GUID': person_tag_0['GUID'],
        'type': 'PERSON',
        'name': 'Papscht',
        'start_char': 4,
        'stop_char': 11
    }

@pytest.fixture
def place_tag_0():
    return {
        'GUID': str(uuid4()),
        'type': 'PLACE',
        'name': 'Spiez',
        'start_char': 19,
        'stop_char': 24,
        'longitude': 1.5346,
        'latitude': 48.2348
    }

@pytest.fixture
def place_tag_1(place_tag_0):
    return {
        'GUID': place_tag_0['GUID'],
        'type': 'PLACE',
        'name': 'Spiez',
        'start_char': 19,
        'stop_char': 24
    }

@pytest.fixture
def time_tag_0():
    return {
        'GUID': str(uuid4()),
        'type': 'TIME',
        'name': '1999:1:1:1',
        'start_char': 19,
        'stop_char': 24
    }

@pytest.fixture
def time_tag_1(time_tag_0):
    return {
        'GUID': time_tag_0['GUID'],
        'type': 'TIME',
        'name': '1999:1:1:1',
        'start_char': 19,
        'stop_char': 24
    }

@pytest.fixture
def summary_guid():
    return str(uuid4())

@pytest.fixture
def summary_new(summary_guid):
    return {
        'GUID': summary_guid,
        'text': 'here is some long text indicating a person, place, and time'
    }

@pytest.fixture
def summary_existing(summary_guid):
    return {
        'GUID': summary_guid
    }

# sad paths

def test_raises_error_with_unknown_type(handler):
    with pytest.raises(UnknownCommandTypeError):
        handler.handle_command({'type': 'who knows!'})

def test_raises_error_with_missing_fields(handler):
    with pytest.raises(CitationMissingFieldsError):
        handler.handle_command({
            'type': 'PUBLISH_NEW_CITATION', 
            'something': 'missing here'})

@pytest.mark.asyncio
async def test_raises_error_with_duplicate_citation_text(handler, citation0):
    handler.handle_command(citation0)
    with pytest.raises(CitationExistsError):
        handler.handle_command(citation0)

@pytest.mark.asyncio
async def test_raises_error_with_duplicate_citation_guid(handler, citation0, citation1):
    handler.handle_command(citation0)
    citation1['payload']['GUID'] = citation0['payload']['GUID']
    with pytest.raises(GUIDError):
        handler.handle_command(citation1)

@pytest.mark.asyncio
async def test_raises_error_with_matched_meta_guid(handler, citation0, citation1):
    handler.handle_command(citation0)
    citation1['payload']['meta']['GUID'] = citation0['payload']['GUID']
    with pytest.raises(GUIDError):
        handler.handle_command(citation1)

@pytest.mark.asyncio
async def test_raises_error_with_unknown_tag_type(handler, citation0, person_tag_0):
    person_tag_0['type'] = 'totally unknown'
    citation0['payload']['tags'] = [person_tag_0]
    with pytest.raises(UnknownTagTypeError):
        handler.handle_command(citation0)

@pytest.mark.asyncio
async def test_raises_error_with_tag_with_guid_of_different_type(
    handler, citation0, person_tag_0):

    # give the citation GUID to the tag -- it'll run first and throw an error 
    # for duplication
    person_tag_0['GUID'] = citation0['payload']['GUID']
    citation0['payload']['tags'] = [person_tag_0]
    with pytest.raises(GUIDError):
        handler.handle_command(citation0)

# happy paths!

@pytest.mark.asyncio
async def test_accepts_command_with_equal_meta_guid(
    handler, citation0, citation1):
    handler.handle_command(citation0)
    citation1['payload']['meta'] = citation0['payload']['meta']
    handler.handle_command(citation1)

@pytest.mark.asyncio
async def test_adds_person_when_given_new_person_guid(
    handler, citation0, person_tag_0):
    citation0['payload']['tags'] = [person_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['TIME_TAGGED', 'TIME_ADDED', 'PLACE_ADDED', 'PLACE_TAGGED']
    assert any(t['type'] == 'PERSON_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'PERSON_TAGGED' for t in synthetic_events) == False
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_tags_person_when_given_a_known_person_guid(
    handler, citation0, person_tag_0, person_tag_1):
    citation0['payload']['tags'] = [person_tag_0, person_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['TIME_TAGGED', 'TIME_ADDED', 'PLACE_ADDED', 'PLACE_TAGGED']
    assert any(t['type'] == 'PERSON_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'PERSON_TAGGED' for t in synthetic_events) == True
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_adds_place_when_given_new_place_guid(
    handler, citation0, place_tag_0):
    citation0['payload']['tags'] = [place_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['TIME_TAGGED', 'TIME_ADDED', 'PERSON_ADDED', 'PERSON_TAGGED']
    assert any(t['type'] == 'PLACE_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'PLACE_TAGGED' for t in synthetic_events) == False
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_tags_place_when_given_a_known_place_guid(
    handler, citation0, place_tag_0, place_tag_1):
    citation0['payload']['tags'] = [place_tag_0, place_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['TIME_TAGGED', 'TIME_ADDED', 'PERSON_ADDED', 'PERSON_TAGGED']
    assert any(t['type'] == 'PLACE_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'PLACE_TAGGED' for t in synthetic_events) == True
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_adds_time_when_given_new_time_guid(
    handler, citation0, time_tag_0):
    citation0['payload']['tags'] = [time_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['PLACE_TAGGED', 'PLACE_ADDED', 'PERSON_ADDED', 'PERSON_TAGGED']
    assert any(t['type'] == 'TIME_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'TIME_TAGGED' for t in synthetic_events) == False
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_tags_time_when_given_a_known_time_guid(
    handler, citation0, time_tag_0, time_tag_1):
    citation0['payload']['tags'] = [time_tag_0, time_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ['PLACE_TAGGED', 'PLACE_ADDED', 'PERSON_ADDED', 'PERSON_TAGGED']
    assert any(t['type'] == 'TIME_ADDED' for t in synthetic_events) == True
    assert any(t['type'] == 'TIME_TAGGED' for t in synthetic_events) == True
    assert any(t['type'] in OTHER for t in synthetic_events) == False

@pytest.mark.asyncio
async def test_synthetic_event(
    handler, citation0, person_tag_0, person_tag_1, place_tag_0, place_tag_1,
    time_tag_0, time_tag_1):
    tags = [person_tag_0, person_tag_1, place_tag_0, place_tag_1, time_tag_0, time_tag_1]
    citation0['payload']['tags'] = tags
    synthetic_events = handler.handle_command(citation0)
    # there are currently 9 types of synthetic tags, and this should 
    # include all of them
    assert len(synthetic_events) == 9
    expected_types = ['SUMMARY_ADDED', 'CITATION_ADDED', 'PERSON_ADDED', 'PERSON_TAGGED', 
        'PLACE_ADDED', 'PLACE_TAGGED', 'TIME_ADDED', 'TIME_TAGGED',
        'META_ADDED']
    for t, s in zip(expected_types, synthetic_events):
        assert t == s['type']
