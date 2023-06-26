from logging import getLogger
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from abstract_domain_model.models import (
    PersonAdded,
    PersonAddedPayload,
    CitationAddedPayload,
    CitationAdded,
    PersonTaggedPayload,
    PersonTagged,
    TimeAddedPayload,
    TimeAdded,
    TimeTaggedPayload,
    TimeTagged,
    PlaceAddedPayload,
    PlaceAdded,
    PlaceTaggedPayload,
    PlaceTagged,
)
from server.the_history_atlas import AnnotatedCitation
from server.the_history_atlas import Entity

log = getLogger(__name__)

ENTITIES = {"PERSON", "PLACE", "TIME"}


event_base_dict = {
    "transaction_id": "2aab2a27-6b61-47d3-b5ba-a5057d0a880c",
    "app_version": "0.0.1-test",
    "timestamp": "2022-08-14 04:21:20.043861",
    "user_id": "a90de541-1455-45c5-ac51-915b93ff057f",
}


@pytest.fixture
def citation_added():
    text = "After 1605 Kapsberger moved to Rome, where he quickly attained a reputation as a brilliant virtuoso."
    payload = CitationAddedPayload(
        id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        text=text,
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        meta_id="d4640c23-e491-4b17-a01b-2bb5e0ea0662",
    )
    return CitationAdded(**event_base_dict, payload=payload)


@pytest.fixture
def person_added():
    payload = PersonAddedPayload(
        id="74415953-e291-4c4d-a275-d8fd75710dc6",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="Kapsberger",
        citation_start=11,
        citation_end=21,
    )
    return PersonAdded(**event_base_dict, payload=payload)


@pytest.fixture
def person_tagged():
    payload = PersonTaggedPayload(
        id="74415953-e291-4c4d-a275-d8fd75710dc6",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="Kapsberger",
        citation_start=11,
        citation_end=21,
    )
    return PersonTagged(**event_base_dict, payload=payload)


@pytest.fixture
def time_added():
    payload = TimeAddedPayload(
        id="fc1fcb77-7a5c-474e-902f-71049c864a51",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="1605",
        citation_start=6,
        citation_end=10,
    )
    return TimeAdded(**event_base_dict, payload=payload)


@pytest.fixture
def time_tagged():
    payload = TimeTaggedPayload(
        id="fc1fcb77-7a5c-474e-902f-71049c864a51",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="1605",
        citation_start=6,
        citation_end=10,
    )
    return TimeTagged(**event_base_dict, payload=payload)


@pytest.fixture
def place_added():
    payload = PlaceAddedPayload(
        id="c7eee9cb-ae18-4382-9a23-0ea88729413b",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="Rome",
        citation_start=31,
        citation_end=35,
        longitude=12.4964,
        latitude=41.9028,
        geo_shape=None,
    )
    return PlaceAdded(**event_base_dict, payload=payload)


@pytest.fixture
def place_tagged():
    payload = PlaceTaggedPayload(
        id="c7eee9cb-ae18-4382-9a23-0ea88729413b",
        citation_id="efb1266e-4b79-437e-9fdb-b0e62eb2de3b",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="Rome",
        citation_start=31,
        citation_end=35,
    )
    return PlaceTagged(**event_base_dict, payload=payload)


def test_db_content(db):
    with Session(db._engine, future=True) as session:
        annotated_citations = session.execute(select(AnnotatedCitation)).scalars()
        # there are results, right?
        assert len([r.id for r in annotated_citations]) > 0
        tags = session.execute(select(Entity)).scalars()
        # there are results, right?
        assert len([r.id for r in tags]) > 0


def test_get_training_corpus(db):
    res = db.get_training_corpus()
    assert res != None
    # replicate the standard access pattern
    for text, entities in res:
        assert isinstance(text, str)
        assert isinstance(entities, list)
        for start, stop, label in entities:
            assert isinstance(stop, int)
            assert isinstance(start, int)
            assert isinstance(label, str)
            assert label in ENTITIES


def test_handle_citation_added(db, citation_added):
    db._handle_citation_added(citation_added)
    with Session(db._engine, future=True) as session:
        citation = (
            session.query(AnnotatedCitation)
            .filter(AnnotatedCitation.id == citation_added.payload.id)
            .one()
        )
        assert str(citation.id) == citation_added.payload.id
        assert citation.text == citation_added.payload.text


@pytest.mark.parametrize(
    "event",
    [
        "person_added",
        "person_tagged",
        "place_added",
        "place_tagged",
        "time_added",
        "time_tagged",
    ],
)
def test_handle_entity_tagged(event, db, citation_added, request):
    event = request.getfixturevalue(event)
    db._handle_citation_added(citation_added)
    db._handle_entity_tagged(event)
    with Session(db._engine, future=True) as session:
        entity = session.query(Entity).filter(Entity.id == event.payload.id).one()
        assert str(entity.id) == event.payload.id
        assert entity.start_char == event.payload.citation_start
        assert entity.stop_char == event.payload.citation_end
        assert str(entity.annotated_citation_id) == event.payload.citation_id
        assert entity.type in event.type  # ex. "TIME" in "TIME_TAGGED"


def test_handle_entity_tagged_fails_gracefully_on_integrity_error(db, person_added):
    db._handle_entity_tagged(person_added)
    with Session(db._engine, future=True) as session:
        entity = (
            session.query(Entity)
            .filter(Entity.id == person_added.payload.id)
            .one_or_none()
        )
        assert entity is None


@patch("nlp_service.state.database.Database._handle_citation_added")
def test_handle_event_calls_handle_citation_added(func, db, citation_added):
    db.handle_event(citation_added)
    func.assert_called_with(citation_added)


@pytest.mark.parametrize(
    "event",
    [
        "person_added",
        "person_tagged",
        "place_added",
        "place_tagged",
        "time_added",
        "time_tagged",
    ],
)
@patch("nlp_service.state.database.Database._handle_entity_tagged")
def test_handle_event_calls_handle_entity_tagged(func, event, db, request):
    event = request.getfixturevalue(event)
    db.handle_event(event)
    func.assert_called_with(event)


@patch("nlp_service.state.database.Database._handle_citation_added")
@patch("nlp_service.state.database.Database._handle_entity_tagged")
def test_handle_event_does_nothing_with_unknown_event(
    handle_entity_tagged, handle_citation_added, db
):
    event = MagicMock()
    db.handle_event(event)
    handle_entity_tagged.assert_not_called()
    handle_citation_added.assert_not_called()
