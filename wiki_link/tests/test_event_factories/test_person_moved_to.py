"""Tests for the PersonMovedTo event factory."""

from unittest.mock import Mock

import pytest

from wiki_service.event_factories.person_moved_to import PersonMovedTo
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    RESIDENCE,
    START_TIME,
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
    coordinates = CoordinateLocation(
        id="Q12345$COORDINATE_ID",
        rank="normal",
        type="statement",
        snaktype="value",
        property="P625",
        hash="some_hash",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=None,
        precision=0.0001,
        globe="http://www.wikidata.org/entity/Q2",
    )
    geo_location = GeoLocation(coordinates=coordinates, geoshape=None)
    query.get_geo_location.return_value = geo_location
    return query


def test_entity_has_event_no_claims(mock_entity, mock_query):
    mock_entity.claims = {}
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_no_start_time(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
            }
        ]
    }
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_with_start_time(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event()


def test_create_wiki_event_basic(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person moved to Test City in 1990."
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Test City"
    assert event.time_tag.time_definition.time == "+1990-01-01T00:00:00Z"


def test_create_wiki_event_male_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
        ],
        SEX_OR_GENDER: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": MALE}},
                },
            }
        ],
    }
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person moved to Test City in 1990."


def test_create_wiki_event_female_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
        ],
        SEX_OR_GENDER: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": FEMALE}},
                },
            }
        ],
    }
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person moved to Test City in 1990."


def test_create_wiki_event_day_precision(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "On June 15, 1990, Test Person moved to Test City."


def test_create_wiki_event_no_location_data(mock_entity, mock_query):
    mock_entity.claims = {
        RESIDENCE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
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
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
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
                    START_TIME: [
                        {
                            "property": START_TIME,
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
    factory = PersonMovedTo(entity=mock_entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError, match="Unexpected time precision: 8"):
        factory.create_wiki_event()
