"""Tests for the PersonMovedAwayFrom event factory."""

from unittest.mock import Mock

import pytest

from wiki_service.event_factories.person_moved_away_from import PersonMovedAwayFrom
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    RESIDENCE,
    END_TIME,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
)
from wiki_service.wikidata_query_service import GeoLocation, CoordinateLocation


@pytest.fixture
def mock_entity():
    entity = Mock()
    entity.id = "Q123"
    entity.labels = {"en": Mock(value="Test Person")}
    return entity


@pytest.fixture
def mock_query():
    query = Mock()
    query.get_label.return_value = "Test City"
    query.get_geo_location.return_value = GeoLocation(
        coordinates=CoordinateLocation(
            id="Q456$COORDINATE_ID",
            rank="normal",
            type="statement",
            snaktype="value",
            property="P625",
            hash="some_hash",
            latitude=0,
            longitude=0,
            altitude=None,
            precision=0.0001,
            globe="http://www.wikidata.org/entity/Q2",
        ),
        geoshape=None,
    )
    return query


def test_entity_has_event_no_claims(mock_entity, mock_query):
    mock_entity.claims = {}
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_no_end_time(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
            }
        ]
    }
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_with_end_time(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": (
                                        "http://www.wikidata.org/entity/Q1985727"
                                    ),
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event()


def test_create_wiki_event_basic(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": (
                                        "http://www.wikidata.org/entity/Q1985727"
                                    ),
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person moved away from Test City in 1990."
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Test City"
    assert event.time_tag.time_definition.time == "+1990-01-01T00:00:00Z"


def test_create_wiki_event_day_precision(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-06-15T00:00:00Z",
                                    "precision": 11,
                                    "calendarmodel": (
                                        "http://www.wikidata.org/entity/Q1985727"
                                    ),
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "On June 15, 1990, Test Person moved away from Test City."


def test_create_wiki_event_no_location_data(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": (
                                        "http://www.wikidata.org/entity/Q1985727"
                                    ),
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    mock_query.get_geo_location.return_value = GeoLocation(
        coordinates=None, geoshape=None
    )
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 0


def test_create_wiki_event_invalid_precision(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 8,  # Decade precision
                                    "calendarmodel": (
                                        "http://www.wikidata.org/entity/Q1985727"
                                    ),
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonMovedAwayFrom(entity=mock_entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError, match="Unexpected time precision: 8"):
        factory.create_wiki_event()
