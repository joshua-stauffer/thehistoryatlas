import os
from copy import deepcopy
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from uuid import uuid4

from abstract_domain_model.models.commands.publish_citation import (
    Time,
    Person,
    Place,
    PublishCitation,
)
from writemodel.state_manager.command_handler import CommandHandler
from writemodel.state_manager.database import Database
from writemodel.state_manager.text_processor import TextHasher
from writemodel.state_manager.handler_errors import (
    GUIDError,
    UnknownCommandTypeError,
    CitationMissingFieldsError,
    CitationExistsError,
    UnknownTagTypeError,
)


@pytest.fixture
def hash_text():
    t = TextHasher()
    return t.get_hash


@pytest.fixture
def handler(db, hash_text):
    return CommandHandler(database_instance=db, hash_text=hash_text)


@pytest.fixture
def handler_with_mock_db(mock_db, hash_text):
    return CommandHandler(database_instance=mock_db, hash_text=hash_text)


@pytest.fixture
def basic_meta():
    return {
        "type": "PUBLISH_NEW_CITATION",
        "user": "da schwitz",
        "timestamp": "2022-08-15 21:32:28.133457",
        "app_version": "0.0.0",
    }


@pytest.fixture
def meta0():
    return {
        # "GUID": "917ddfcf-8feb-4755-bc40-144c8351b7cd",
        "author": "francesco, natürli",
        "publisher": "dr papscht",
        "title": "try this at home",
    }


@pytest.fixture
def citation0(basic_meta, meta0, summary_new):
    return {
        **basic_meta,
        "payload": {
            "GUID": "917ddfcf-8feb-4755-bc40-144c8351b7cd",
            "text": "Dr Papscht hett ds Spiez Späck Besteck spät bestellt",
            "tags": [],
            "meta": meta0,
            "summary": summary_new,
        },
    }


@pytest.fixture
def meta1():
    return {
        # "GUID": "917ddfcf-8feb-4755-bc40-144c8351b7cd",
        "author": "francesco, natürli",
        "publisher": "dr papscht",
        "title": "try this at home",
    }


@pytest.fixture
def citation1(basic_meta, meta1, summary_existing):
    return {
        **basic_meta,
        "payload": {
            "GUID": "42891176-dd66-4775-8f4a-82e03652cc2d",
            # this text has an extra letter, so is considered unique
            "text": "Der Papscht hett ds Spiez Späck Besteck spät bestellt",
            "tags": [],
            "meta": meta1,
            "summary": summary_existing,
        },
    }


@pytest.fixture
def person_tag_0():
    return {
        "type": "PERSON",
        "name": "Papscht",
        "start_char": 3,
        "stop_char": 10,
    }


@pytest.fixture
def person_tag_1(person_tag_0, existing_person_id):
    return {
        "GUID": existing_person_id,
        "type": "PERSON",
        "name": "Papscht",
        "start_char": 4,
        "stop_char": 11,
    }


@pytest.fixture
def place_tag_0():
    return {
        "type": "PLACE",
        "name": "Spiez",
        "start_char": 19,
        "stop_char": 24,
        "longitude": 1.5346,
        "latitude": 48.2348,
    }


@pytest.fixture
def place_tag_1(existing_place_id):
    return {
        "GUID": existing_place_id,
        "type": "PLACE",
        "name": "Spiez",
        "start_char": 19,
        "stop_char": 24,
        "latitude": 1.234,
        "longitude": 2.345,
        "geo_shape": None,
    }


@pytest.fixture
def time_tag_0():
    return {
        "type": "TIME",
        "name": "1999:1:1:1",
        "start_char": 19,
        "stop_char": 24,
    }


@pytest.fixture
def time_tag_1(existing_time_id):
    return {
        "GUID": existing_time_id,
        "type": "TIME",
        "name": "1999:1:1:1",
        "start_char": 19,
        "stop_char": 24,
    }


@pytest.fixture
def summary_guid():
    return str(uuid4())


@pytest.fixture
def summary_new(summary_guid):
    return {
        # "GUID": summary_guid,
        "text": "here is some long text indicating a person, place, and time",
    }


@pytest.fixture
def summary_existing(existing_summary_id):
    return {"GUID": existing_summary_id}


def test_raises_error_with_unknown_type(handler):
    with pytest.raises(UnknownCommandTypeError):
        handler.handle_command({"type": "who knows!"})


def test_raises_error_with_missing_fields(handler):
    with pytest.raises(CitationMissingFieldsError):
        handler.handle_command(
            {"type": "PUBLISH_NEW_CITATION", "something": "missing here"}
        )


@pytest.mark.asyncio
async def test_raises_error_with_duplicate_citation_text(handler, citation0):
    handler.handle_command(citation0)
    with pytest.raises(CitationExistsError):
        handler.handle_command(citation0)


@pytest.mark.asyncio
async def test_raises_error_with_matched_meta_guid(
    handler, citation0, citation1, existing_summary_id
):
    handler.handle_command(citation0)
    citation1["payload"]["meta"]["GUID"] = existing_summary_id
    with pytest.raises(GUIDError):
        handler.handle_command(citation1)


@pytest.mark.asyncio
async def test_raises_error_with_unknown_tag_type(handler, citation0, person_tag_0):
    person_tag_0["type"] = "totally unknown"
    citation0["payload"]["tags"] = [person_tag_0]
    with pytest.raises(UnknownTagTypeError):
        handler.handle_command(citation0)


@pytest.mark.asyncio
async def test_raises_error_with_tag_with_guid_of_different_type(
    handler, citation0, person_tag_0, existing_meta_id
):
    # give the citation GUID to the tag -- it'll run first and throw an error
    # for duplication
    person_tag_0["GUID"] = existing_meta_id
    citation0["payload"]["tags"] = [person_tag_0]
    with pytest.raises(GUIDError):
        handler.handle_command(citation0)


@pytest.mark.asyncio
async def test_accepts_command_with_equal_meta_guid(handler, citation0, citation1):
    handler.handle_command(citation0)
    citation1["payload"]["meta"] = citation0["payload"]["meta"]
    handler.handle_command(citation1)


@pytest.mark.asyncio
async def test_adds_person_when_given_new_person_guid(handler, citation0, person_tag_0):
    citation0["payload"]["tags"] = [person_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["TIME_TAGGED", "TIME_ADDED", "PLACE_ADDED", "PLACE_TAGGED"]
    assert any(t["type"] == "PERSON_ADDED" for t in synthetic_events) is True
    assert any(t["type"] == "PERSON_TAGGED" for t in synthetic_events) is False
    assert any(t["type"] in OTHER for t in synthetic_events) is False


@pytest.mark.asyncio
async def test_tags_person_when_given_a_known_person_guid(
    handler, citation0, person_tag_0, person_tag_1
):
    citation0["payload"]["tags"] = [person_tag_0, person_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["TIME_TAGGED", "TIME_ADDED", "PLACE_ADDED", "PLACE_TAGGED"]
    assert any(t["type"] == "PERSON_ADDED" for t in synthetic_events) is True
    assert any(t["type"] == "PERSON_TAGGED" for t in synthetic_events) is True
    assert any(t["type"] in OTHER for t in synthetic_events) is False


@pytest.mark.asyncio
async def test_adds_place_when_given_new_place_guid(handler, citation0, place_tag_0):
    citation0["payload"]["tags"] = [place_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["TIME_TAGGED", "TIME_ADDED", "PERSON_ADDED", "PERSON_TAGGED"]
    assert any(t["type"] == "PLACE_ADDED" for t in synthetic_events) == True
    assert any(t["type"] == "PLACE_TAGGED" for t in synthetic_events) == False
    assert any(t["type"] in OTHER for t in synthetic_events) == False


@pytest.mark.asyncio
async def test_tags_place_when_given_a_known_place_guid(
    handler, citation0, place_tag_0, place_tag_1
):
    citation0["payload"]["tags"] = [place_tag_0, place_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["TIME_TAGGED", "TIME_ADDED", "PERSON_ADDED", "PERSON_TAGGED"]
    assert any(t["type"] == "PLACE_ADDED" for t in synthetic_events) == True
    assert any(t["type"] == "PLACE_TAGGED" for t in synthetic_events) == True
    assert any(t["type"] in OTHER for t in synthetic_events) == False


@pytest.mark.asyncio
async def test_adds_time_when_given_new_time_guid(handler, citation0, time_tag_0):
    citation0["payload"]["tags"] = [time_tag_0]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["PLACE_TAGGED", "PLACE_ADDED", "PERSON_ADDED", "PERSON_TAGGED"]
    assert any(t["type"] == "TIME_ADDED" for t in synthetic_events) == True
    assert any(t["type"] == "TIME_TAGGED" for t in synthetic_events) == False
    assert any(t["type"] in OTHER for t in synthetic_events) == False


@pytest.mark.asyncio
async def test_tags_time_when_given_a_known_time_guid(
    handler, citation0, time_tag_0, time_tag_1
):
    citation0["payload"]["tags"] = [time_tag_0, time_tag_1]
    synthetic_events = handler.handle_command(citation0)
    OTHER = ["PLACE_TAGGED", "PLACE_ADDED", "PERSON_ADDED", "PERSON_TAGGED"]
    assert any(t["type"] == "TIME_ADDED" for t in synthetic_events) == True
    assert any(t["type"] == "TIME_TAGGED" for t in synthetic_events) == True
    assert any(t["type"] in OTHER for t in synthetic_events) == False


@pytest.mark.asyncio
async def test_synthetic_event(
    handler,
    citation0,
    person_tag_0,
    person_tag_1,
    place_tag_0,
    place_tag_1,
    time_tag_0,
    time_tag_1,
):
    tags = [
        person_tag_0,
        person_tag_1,
        place_tag_0,
        place_tag_1,
        time_tag_0,
        time_tag_1,
    ]
    citation0["payload"]["tags"] = tags
    synthetic_events = handler.handle_command(citation0)
    # there are currently 9 types of synthetic tags, and this should
    # include all of them
    assert len(synthetic_events) == 9
    expected_types = [
        "SUMMARY_ADDED",
        "CITATION_ADDED",
        "PERSON_ADDED",
        "PERSON_TAGGED",
        "PLACE_ADDED",
        "PLACE_TAGGED",
        "TIME_ADDED",
        "TIME_TAGGED",
        "META_ADDED",
    ]
    for t, s in zip(expected_types, synthetic_events):
        assert t == s["type"]


def test_translate_time(handler_with_mock_db, time_tag_0):
    tag = handler_with_mock_db._translate_time(time_tag_0)
    assert isinstance(tag, Time)


def test_translate_person(handler_with_mock_db, person_tag_0):
    tag = handler_with_mock_db._translate_person(person_tag_0)
    assert isinstance(tag, Person)


def test_translate_place(handler_with_mock_db, place_tag_0):
    tag = handler_with_mock_db._translate_place(place_tag_0)
    assert isinstance(tag, Place)


@patch("writemodel.state_manager.command_handler.CommandHandler._translate_person")
def test_translate_tag_returns_person(
    translate_method, person_tag_0, handler_with_mock_db
):
    handler_with_mock_db._translate_tag(person_tag_0)
    translate_method.assert_called_with(person_tag_0)


@patch("writemodel.state_manager.command_handler.CommandHandler._translate_time")
def test_translate_tag_returns_time(translate_method, time_tag_0, handler_with_mock_db):
    handler_with_mock_db._translate_tag(time_tag_0)
    translate_method.assert_called_with(time_tag_0)


@patch("writemodel.state_manager.command_handler.CommandHandler._translate_place")
def test_translate_tag_returns_place(
    translate_method, place_tag_0, handler_with_mock_db
):
    handler_with_mock_db._translate_tag(place_tag_0)
    translate_method.assert_called_with(place_tag_0)


@pytest.mark.parametrize("tag", ({}, {"type": "UNKNOWN"}, {"random": "field"}))
def test_translate_tag_raises_exception_with_unknown_input(tag, handler_with_mock_db):
    with pytest.raises(UnknownTagTypeError):
        handler_with_mock_db._translate_tag(tag)


def test_translate_publish_citation_without_tags(handler_with_mock_db, citation0):
    command = handler_with_mock_db._translate_publish_citation(citation0)
    assert isinstance(command, PublishCitation)


def test_translate_publish_citation_with_tags(
    handler_with_mock_db, citation0, time_tag_0, person_tag_0, place_tag_0
):
    citation = deepcopy(citation0)
    citation["payload"]["tags"] = [time_tag_0, person_tag_0, place_tag_0]
    command = handler_with_mock_db._translate_publish_citation(citation0)
    assert isinstance(command, PublishCitation)


def test_translate_command_success(handler_with_mock_db, citation0):
    command = handler_with_mock_db.translate_command(citation0)
    assert isinstance(command, PublishCitation)


@pytest.mark.parametrize("citation", ({}, {"type": "UNKNOWN"}, {"random": "field"}))
def test_translate_command_failure(citation, handler_with_mock_db):
    with pytest.raises(UnknownCommandTypeError):
        _ = handler_with_mock_db.translate_command(citation)
