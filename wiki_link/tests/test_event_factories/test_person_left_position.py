"""Tests for the PersonLeftPosition event factory."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, call

from wiki_service.event_factories.person_left_position import PersonLeftPosition
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    POSITION_HELD,
    END_TIME,
    COORDINATE_LOCATION,
    WORK_LOCATION,
    ELECTORAL_DISTRICT,
    REPRESENTS,
    APPLIES_TO_JURISDICTION,
    REPLACED_BY,
)
from wiki_service.types import (
    Entity,
    GeoLocation,
    Query,
    TimeDefinition,
    Property,
    CoordinateLocation,
)


class MockQuery:
    def get_label(self, id: str, language: str) -> str:
        labels = {
            "Q1": "Barack Obama",
            "Q2": "President of the United States",
            "Q3": "White House",
            "Q4": "Joe Biden",
            "Q5": "Governor of California",
            "Q6": "California State Capitol",
            "Q7": "California",
            "Q8": "Arnold Schwarzenegger",
            "Q9": "Jerry Brown",
            "Q10": "Mayor of New York City",
            "Q11": "City Hall",
            "Q12": "New York City",
            "Q13": "Bill de Blasio",
        }
        return labels.get(id, f"Unknown ({id})")

    def get_geo_location(self, id: str) -> GeoLocation:
        locations = {
            "Q3": GeoLocation(  # White House
                coordinates=CoordinateLocation(
                    id=f"{id}$COORDINATE_ID",
                    rank="normal",
                    type="statement",
                    snaktype="value",
                    property="P625",
                    hash="some_hash",
                    latitude=38.8977,
                    longitude=-77.0365,
                    altitude=None,
                    precision=0.0001,
                    globe="http://www.wikidata.org/entity/Q2",
                ),
                geoshape=None,
            ),
            "Q6": GeoLocation(  # CA Capitol
                coordinates=CoordinateLocation(
                    id=f"{id}$COORDINATE_ID",
                    rank="normal",
                    type="statement",
                    snaktype="value",
                    property="P625",
                    hash="some_hash",
                    latitude=38.5766,
                    longitude=-121.4934,
                    altitude=None,
                    precision=0.0001,
                    globe="http://www.wikidata.org/entity/Q2",
                ),
                geoshape=None,
            ),
            "Q11": GeoLocation(  # NYC City Hall
                coordinates=CoordinateLocation(
                    id=f"{id}$COORDINATE_ID",
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
                ),
                geoshape=None,
            ),
        }
        return locations.get(id, GeoLocation(coordinates=None, geoshape=None))

    def get_entity(self, id: str) -> Entity:
        entities = {
            "Q2": Entity(  # President
                id="Q2",
                type="item",
                pageid=123,
                ns=0,
                title="Q2",
                lastrevid=456,
                modified="2024-04-01T00:00:00Z",
                labels={
                    "en": Property(
                        language="en", value="President of the United States"
                    )
                },
                descriptions={"en": Property(language="en", value="Head of state")},
                aliases={"en": [Property(language="en", value="POTUS")]},
                claims={
                    WORK_LOCATION: [
                        {
                            "mainsnak": {
                                "datavalue": {"value": {"id": "Q3"}},  # White House
                            }
                        }
                    ]
                },
                sitelinks={},
            ),
            "Q5": Entity(  # Governor
                id="Q5",
                type="item",
                pageid=124,
                ns=0,
                title="Q5",
                lastrevid=457,
                modified="2024-04-01T00:00:00Z",
                labels={"en": Property(language="en", value="Governor of California")},
                descriptions={"en": Property(language="en", value="State governor")},
                aliases={"en": []},
                claims={
                    WORK_LOCATION: [
                        {
                            "mainsnak": {
                                "datavalue": {"value": {"id": "Q6"}},  # Capitol
                            }
                        }
                    ],
                    APPLIES_TO_JURISDICTION: [
                        {
                            "mainsnak": {
                                "datavalue": {"value": {"id": "Q7"}},  # California
                            }
                        }
                    ],
                },
                sitelinks={},
            ),
            "Q10": Entity(  # Mayor
                id="Q10",
                type="item",
                pageid=125,
                ns=0,
                title="Q10",
                lastrevid=458,
                modified="2024-04-01T00:00:00Z",
                labels={"en": Property(language="en", value="Mayor of New York City")},
                descriptions={"en": Property(language="en", value="City mayor")},
                aliases={"en": []},
                claims={
                    WORK_LOCATION: [
                        {
                            "mainsnak": {
                                "datavalue": {"value": {"id": "Q11"}},  # City Hall
                            }
                        }
                    ],
                    REPRESENTS: [
                        {
                            "mainsnak": {
                                "datavalue": {"value": {"id": "Q12"}},  # NYC
                            }
                        }
                    ],
                },
                sitelinks={},
            ),
        }
        return entities.get(id)


@pytest.fixture
def mock_query():
    mock = Mock()

    def get_label_side_effect(id, language):
        labels = {
            "Q456": "Test Position",
            "Q789": "Test Location",
            "Q999": "Test Replacement Person",
        }
        return labels.get(id, "Test Label")

    mock.get_label.side_effect = get_label_side_effect

    def get_geo_location_side_effect(id):
        if id == "Q789":
            return GeoLocation(
                coordinates=CoordinateLocation(
                    id=f"{id}$COORDINATE_ID",
                    rank="normal",
                    type="statement",
                    snaktype="value",
                    property="P625",
                    hash="some_hash",
                    latitude=0.0,
                    longitude=0.0,
                    altitude=None,
                    precision=0.0001,
                    globe="http://www.wikidata.org/entity/Q2",
                ),
                geoshape=None,
            )
        return None

    mock.get_geo_location.side_effect = get_geo_location_side_effect
    mock.get_entity.return_value = Entity(
        id="Q456",
        pageid=123,
        ns=0,
        title="Q456",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Position")},
        descriptions={},
        aliases={},
        claims={},
        sitelinks={},
    )
    return mock


def test_version():
    factory = PersonLeftPosition(entity=Mock(), query=Mock(), entity_type="PERSON")
    assert factory.version == 0


def test_label():
    factory = PersonLeftPosition(entity=Mock(), query=Mock(), entity_type="PERSON")
    assert factory.label == "Person left position"


def test_entity_has_event_wrong_type():
    entity = Mock()
    factory = PersonLeftPosition(entity=entity, query=Mock(), entity_type="LOCATION")
    assert not factory.entity_has_event()


def test_entity_has_event_no_claims():
    entity = Mock()
    entity.claims = {}
    factory = PersonLeftPosition(entity=entity, query=Mock(), entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_no_end_time():
    entity = Mock()
    entity.claims = {
        "P39": [{"mainsnak": {"datavalue": {"value": {"id": "Q123"}}}}]  # POSITION_HELD
    }
    factory = PersonLeftPosition(entity=entity, query=Mock(), entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_with_end_time():
    entity = Mock()
    entity.claims = {
        "P39": [  # POSITION_HELD
            {
                "mainsnak": {"datavalue": {"value": {"id": "Q123"}}},
                "qualifiers": {
                    "P582": [  # END_TIME
                        {
                            "hash": "hash123",
                            "snaktype": "value",
                            "property": "P582",
                            "datavalue": {
                                "value": {
                                    "time": "+2020-01-01T00:00:00Z",
                                    "timezone": 0,
                                    "before": 0,
                                    "after": 0,
                                    "precision": 11,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonLeftPosition(entity=entity, query=Mock(), entity_type="PERSON")
    assert factory.entity_has_event()


def test_create_wiki_event_basic(mock_query):
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        "P937": [  # WORK_LOCATION
                            {"datavalue": {"value": {"id": "Q789"}}}
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]

    assert "Test Person" in event.summary
    assert "Test Position" in event.summary  # Position name
    assert "January 1, 2020" in event.summary
    assert "left the position" in event.summary

    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[0].wiki_id == "Q123"

    assert event.place_tag is not None
    assert event.place_tag.name == "Test Location"
    assert event.place_tag.wiki_id == "Q789"
    assert event.place_tag.location.coordinates.latitude == 0.0
    assert event.place_tag.location.coordinates.longitude == 0.0

    assert event.time_tag is not None
    assert "January 1, 2020" in event.time_tag.name
    assert event.time_tag.time_definition.precision == 11


def test_create_wiki_event_no_location_found(mock_query):
    mock_query.get_geo_location.return_value = None

    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError, match="No valid position events found"):
        factory.create_wiki_event()


def test_create_wiki_event_location_from_position_entity(mock_query):
    # Mock the position entity to have a location claim
    mock_query.get_entity.return_value = Entity(
        id="Q456",
        pageid=123,
        ns=0,
        title="Q456",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Position")},
        descriptions={},
        aliases={},
        claims={
            "P131": [  # LOCATED_IN_THE_ADMINISTRATIVE_TERRITORIAL_ENTITY
                {"mainsnak": {"datavalue": {"value": {"id": "Q789"}}}}
            ]
        },
        sitelinks={},
    )

    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]

    assert event.place_tag is not None
    assert event.place_tag.wiki_id == "Q789"


def test_create_wiki_event_with_replaced_by(mock_query):
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        "P937": [  # WORK_LOCATION
                            {"datavalue": {"value": {"id": "Q789"}}}
                        ],
                        "P1366": [  # REPLACED_BY
                            {"datavalue": {"value": {"id": "Q999"}}}
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]

    assert "Test Person" in event.summary
    assert "Test Position" in event.summary
    assert "Test Replacement Person" in event.summary
    assert "being replaced by Test Replacement Person" in event.summary

    # Check that we have two person tags (original person and replacement person)
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[0].wiki_id == "Q123"
    assert event.people_tags[1].name == "Test Replacement Person"
    assert event.people_tags[1].wiki_id == "Q999"


def test_create_wiki_event_month_precision(mock_query):
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 10,  # Month precision
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        "P937": [  # WORK_LOCATION
                            {"datavalue": {"value": {"id": "Q789"}}}
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]

    assert "In January 2020" in event.summary
    assert "Test Person left the position" in event.summary
    assert event.time_tag.time_definition.precision == 10


def test_create_wiki_event_year_precision(mock_query):
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={},
        aliases={},
        claims={
            "P39": [  # POSITION_HELD
                {
                    "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},
                    "qualifiers": {
                        "P582": [  # END_TIME
                            {
                                "hash": "hash123",
                                "snaktype": "value",
                                "property": "P582",
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-00-00T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 9,  # Year precision
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        "P937": [  # WORK_LOCATION
                            {"datavalue": {"value": {"id": "Q789"}}}
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )

    factory = PersonLeftPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]

    assert "In 2020" in event.summary
    assert "Test Person left the position" in event.summary
    assert event.time_tag.time_definition.precision == 9
