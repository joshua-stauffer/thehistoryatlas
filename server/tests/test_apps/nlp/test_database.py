from logging import getLogger
from unittest.mock import patch, MagicMock, Mock
from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.models import (
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
from the_history_atlas.apps.nlp.state.database import Database
from the_history_atlas.apps.nlp.state.schema import AnnotatedCitation
from the_history_atlas.apps.nlp.state.schema import Entity

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
        id="303e74bc-1e60-42a0-8391-f93e8715229f",
        text=text,
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        meta_id="d4640c23-e491-4b17-a01b-2bb5e0ea0662",
    )
    return CitationAdded(**event_base_dict, payload=payload)


@pytest.fixture
def person_added():
    payload = PersonAddedPayload(
        id="74415953-e291-4c4d-a275-d8fd75710dc6",
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
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
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
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
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
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
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
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
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
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
        citation_id="303e74bc-1e60-42a0-8391-f93e8715229f",
        summary_id="ec0c7955-c66e-44ae-82aa-9338d78291c5",
        name="Rome",
        citation_start=31,
        citation_end=35,
    )
    return PlaceTagged(**event_base_dict, payload=payload)


def test_nlp_db_content(nlp_db):
    with Session(nlp_db._engine, future=True) as session:
        annotated_citations = session.execute(select(AnnotatedCitation)).scalars()
        # there are results, right?
        assert len([r.id for r in annotated_citations]) > 0
        tags = session.execute(select(Entity)).scalars()
        # there are results, right?
        assert len([r.id for r in tags]) > 0


def test_get_training_corpus(nlp_db):
    res = nlp_db.get_training_corpus()
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


def test_handle_citation_added(nlp_db, citation_added):
    nlp_db._handle_citation_added(citation_added)
    with Session(nlp_db._engine, future=True) as session:
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
def test_handle_entity(event, nlp_db, citation_added, request, engine):
    event = request.getfixturevalue(event)
    nlp_db.handle_event(citation_added)
    entity_id = UUID(event.payload.id)
    citation_id = UUID(citation_added.payload.id)

    nlp_db.handle_event(event)

    with Session(engine, future=True) as session:
        stmt = text(
            """
            select id, type, start_char, stop_char, annotated_citation_id from entities 
            where entities.id = :id
        """
        )
        (id, type, start_char, stop_char, annotated_citation_id) = session.execute(
            stmt, {"id": entity_id}
        ).one()
        assert id == entity_id
        assert annotated_citation_id == citation_id
        assert start_char == event.payload.citation_start
        assert stop_char == event.payload.citation_end


def test_handle_entity_tagged_fails_gracefully_on_integrity_error(nlp_db, person_added):
    nlp_db._handle_entity_tagged(person_added)
    with Session(nlp_db._engine, future=True) as session:
        entity = (
            session.query(Entity)
            .filter(Entity.id == person_added.payload.id)
            .one_or_none()
        )
        assert entity is None


def test_handle_event_calls_handle_citation_added(nlp_db, citation_added, engine):
    nlp_db.handle_event(citation_added)

    with Session(engine, future=True) as session:
        citation_id = UUID(citation_added.payload.id)
        stmt = text(
            """
            select id, text from annotated_citations
            where annotated_citations.id = :id
        """
        )
        row = session.execute(stmt, {"id": citation_id}).one()
        assert row[0] == citation_id
        assert row[1] == citation_added.payload.text


def test_handle_event_person_added(citation_added, person_added, nlp_db, engine):
    # citation is required first:
    nlp_db.handle_event(citation_added)

    nlp_db.handle_event(person_added)

    with Session(engine, future=True) as session:
        stmt = text(
            """
            select id, type, start_char, stop_char, annotated_citation_id from entities 
            where entities.id = :id
        """
        )
        (id, type, start_char, stop_char, annotated_citation_id) = session.execute(
            stmt, {"id": UUID(person_added.payload.id)}
        ).one()
        assert id == UUID(person_added.payload.id)
        assert annotated_citation_id == UUID(person_added.payload.citation_id)
        assert start_char == person_added.payload.citation_start
        assert stop_char == person_added.payload.citation_end


def test_handle_event_does_nothing_with_unknown_event():
    mock_engine = Mock(autospec=Engine)
    nlp_db = Database(client=mock_engine)
    event = MagicMock()
    nlp_db.handle_event(event)
    mock_engine.assert_not_called()
