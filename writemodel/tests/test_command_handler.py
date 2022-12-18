from copy import deepcopy
from dataclasses import replace, dataclass
from unittest.mock import patch, Mock

import pytest
from uuid import uuid4

from abstract_domain_model.models import (
    PersonAdded,
    PlaceAdded,
    TimeAdded,
    PersonTagged,
    PlaceTagged,
    TimeTagged,
)
from abstract_domain_model.models.commands.publish_citation import (
    Time,
    Person,
    Place,
    PublishCitation,
)
from seed import PUBLISH_CITATIONS
from writemodel.state_manager.command_handler import CommandHandler
from writemodel.state_manager.text_processor import TextHasher
from writemodel.state_manager.handler_errors import (
    GUIDError,
    UnknownCommandTypeError,
    CitationExistsError,
    UnknownTagTypeError,
    MissingResourceError,
)


@pytest.fixture
def hash_text():
    t = TextHasher()
    return t.get_hash


@pytest.fixture
def handler(db, hash_text):
    return CommandHandler(database_instance=db, hash_text=hash_text)


@pytest.fixture
def handler_with_mock_db(hash_text, mock_db):
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


@pytest.fixture
def publish_citation():
    return PUBLISH_CITATIONS[0]


@pytest.fixture
def transaction_meta():
    return {
        "transaction_id": "70ae0538-72a6-44f3-aa15-7a9fa1c199ff",
        "app_version": "0.0.0",
        "user_id": "testy-tester",
        "timestamp": "2022-12-18 21:20:41.262212",
    }


@pytest.mark.asyncio
async def test_validate_publish_citation_success_with_tagged_summary(
    publish_citation, hash_text
):
    """
    If a summary ID is provided, expect it to exist already.
    """
    db = Mock()
    db.check_citation_for_uniqueness.return_value = None
    db.check_id_for_uniqueness.return_value = "SUMMARY"
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            # add an ID so we tag this summary
            summary_id="8f856919-6c46-4837-a41a-69d48c6129a5",
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_success_with_tagged_meta(
    publish_citation, hash_text
):
    """
    If a meta ID is provided, expect it to exist already.
    """
    db = Mock()
    db.check_citation_for_uniqueness.return_value = None
    db.check_id_for_uniqueness.return_value = "META"
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            meta=replace(
                publish_citation.payload.meta,
                # add an ID so we tag this meta
                id="7eee5f0c-14dd-4701-a951-5857beb54405",
            ),
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_success_with_tagged_summary_and_meta(
    publish_citation, hash_text
):
    """
    If both summary ID and meta ID are provided, expect them to exist.
    """
    db = Mock()
    db.check_citation_for_uniqueness.return_value = None
    db.check_id_for_uniqueness.side_effect = ["SUMMARY", "META"]
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            # add an ID so we tag this summary
            summary_id="8f856919-6c46-4837-a41a-69d48c6129a5",
            meta=replace(
                publish_citation.payload.meta,
                # add an ID so we tag this meta
                id="7eee5f0c-14dd-4701-a951-5857beb54405",
            ),
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_citation_exists_error(
    publish_citation, hash_text
):
    """
    If this citation already exists in the system, expect an error.
    """
    db = Mock()
    db.check_citation_for_uniqueness.return_value = "FAILED-UUID-HERE"
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    with pytest.raises(CitationExistsError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_missing_resource_error_for_summary(
    publish_citation, hash_text
):
    """
    If PublishCitation tags a summary that doesn't exist, expect an error.
    """
    db = Mock()
    db.check_citation_for_uniqueness.return_value = None
    db.check_id_for_uniqueness.return_value = None
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            # add an ID so we tag this summary
            summary_id="8f856919-6c46-4837-a41a-69d48c6129a5",
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    with pytest.raises(MissingResourceError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_guid_error_for_summary(
    publish_citation, hash_text
):
    """
    If PublishCitation tags a summary and that ID doesn't belong to a
    Summary, expect an error.
    """
    db = Mock()
    db.check_id_for_uniqueness.return_value = "NOT-SUMMARY"
    db.check_citation_for_uniqueness.return_value = None
    payload = replace(
        publish_citation.payload,
        # add an ID so we tag this summary
        summary_id="8f856919-6c46-4837-a41a-69d48c6129a5",
    )
    publish_citation = replace(publish_citation, payload=payload)
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    with pytest.raises(GUIDError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_missing_resource_error_for_meta(
    publish_citation, hash_text
):
    """
    If PublishCitation tags a Meta, make sure the ID exists.
    """
    db = Mock()
    db.check_id_for_uniqueness.return_value = None
    db.check_citation_for_uniqueness.return_value = None
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            meta=replace(
                publish_citation.payload.meta,
                # add an ID so we tag this meta
                id="7eee5f0c-14dd-4701-a951-5857beb54405",
            ),
        ),
    )

    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    with pytest.raises(MissingResourceError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_guid_error_for_meta(
    publish_citation, hash_text
):
    """
    If PublishCitation tags a Meta and the ID doesn't belong to a Meta,
    expect an error.
    """
    db = Mock()
    db.check_id_for_uniqueness.return_value = "WRONG-TYPE"
    db.check_citation_for_uniqueness.return_value = None
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            meta=replace(
                publish_citation.payload.meta,
                # add an ID so we tag this meta
                id="7eee5f0c-14dd-4701-a951-5857beb54405",
            ),
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)
    with pytest.raises(GUIDError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_missing_resource_error_for_tag(
    publish_citation, hash_text
):
    """
    If a Tag ID is provided, ensure it belongs to an existing Tag.
    """
    db = Mock()
    db.check_id_for_uniqueness.return_value = None
    db.check_citation_for_uniqueness.return_value = None
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            tags=[
                replace(
                    publish_citation.payload.tags[0],
                    id="5f3434ea-f05b-42de-af37-f315c670b90d",
                )
            ],
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)

    with pytest.raises(MissingResourceError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_validate_publish_citation_raises_guid_error_for_tag(
    publish_citation, hash_text
):
    """
    If a Tag ID is provided, ensure it belongs to an existing Tag.
    """
    db = Mock()
    db.check_id_for_uniqueness.side_effect = None
    db.check_citation_for_uniqueness.return_value = None
    publish_citation = replace(
        publish_citation,
        payload=replace(
            publish_citation.payload,
            tags=[
                replace(
                    publish_citation.payload.tags[0],
                    id="5f3434ea-f05b-42de-af37-f315c670b90d",
                )
            ],
        ),
    )
    handler = CommandHandler(database_instance=db, hash_text=hash_text)

    with pytest.raises(GUIDError):
        handler.validate_publish_citation(publish_citation)


@pytest.mark.asyncio
async def test_tag_to_event_raises_error_with_unknown_tag_type(transaction_meta):
    @dataclass
    class NotAnEntity:
        pass

    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"

    with pytest.raises(UnknownTagTypeError):
        CommandHandler.tag_to_event(
            tag=NotAnEntity(),
            transaction_meta=transaction_meta,
            citation_id=citation_id,
            summary_id=summary_id,
        )


@pytest.mark.asyncio
async def test_tag_to_event_adds_person(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Person(
        id=None,
        type="PERSON",
        name="test-person",
        start_char=1,
        stop_char=4,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, PersonAdded)


@pytest.mark.asyncio
async def test_tag_to_event_tags_person(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Person(
        id="d2b578fd-df8b-4ea0-a784-8fbbfdb05c40",
        type="PERSON",
        name="test-person",
        start_char=1,
        stop_char=4,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, PersonTagged)


@pytest.mark.asyncio
async def test_tag_to_event_adds_place(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Place(
        id=None,
        type="PLACE",
        name="test-place",
        start_char=1,
        stop_char=4,
        latitude=1.234,
        longitude=2.345,
        geo_shape=None,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, PlaceAdded)


@pytest.mark.asyncio
async def test_tag_to_event_tags_place(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Place(
        id="d2b578fd-df8b-4ea0-a784-8fbbfdb05c40",
        type="PLACE",
        name="test-place",
        start_char=1,
        stop_char=4,
        latitude=1.234,
        longitude=2.345,
        geo_shape=None,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, PlaceTagged)


@pytest.mark.asyncio
async def test_tag_to_event_adds_time(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Time(
        id=None,
        type="TIME",
        name="test-time",
        start_char=1,
        stop_char=4,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, TimeAdded)


@pytest.mark.asyncio
async def test_tag_to_event_tags_time(transaction_meta):
    citation_id = "a4809b4a-7261-45f4-99fe-f23d9d9885a6"
    summary_id = "842adf92-dd18-4c07-bcd7-5e1ae57da21b"
    entity = Time(
        id="d2b578fd-df8b-4ea0-a784-8fbbfdb05c40",
        type="TIME",
        name="test-time",
        start_char=1,
        stop_char=4,
    )
    event = CommandHandler.tag_to_event(
        tag=entity,
        transaction_meta=transaction_meta,
        summary_id=summary_id,
        citation_id=citation_id,
    )
    assert isinstance(event, TimeTagged)


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
