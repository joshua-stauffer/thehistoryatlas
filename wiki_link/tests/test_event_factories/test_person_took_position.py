"""Tests for the PersonTookPosition event factory."""

import pytest
from datetime import datetime

from wiki_service.event_factories.person_took_position import PersonTookPosition
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    POSITION_HELD,
    START_TIME,
    COORDINATE_LOCATION,
    WORK_LOCATION,
    ELECTORAL_DISTRICT,
    REPRESENTS,
    APPLIES_TO_JURISDICTION,
    REPLACES,
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
            "Q4": "George W. Bush",
            "Q5": "Governor of California",
            "Q6": "California State Capitol",
            "Q7": "California",
            "Q8": "Arnold Schwarzenegger",
            "Q9": "Gray Davis",
            "Q10": "Mayor of New York City",
            "Q11": "City Hall",
            "Q12": "New York City",
            "Q13": "Michael Bloomberg",
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
    return MockQuery()


def test_entity_has_event_true(mock_query):
    """Test that entity_has_event returns True when the entity has a position with start time."""
    entity = Entity(
        id="Q1",
        type="item",
        pageid=123,
        ns=0,
        title="Q1",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Barack Obama")},
        descriptions={
            "en": Property(language="en", value="44th President of the United States")
        },
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q2"}},
                    },
                    "qualifiers": {
                        START_TIME: [
                            {
                                "datavalue": {
                                    "value": {
                                        "time": "+2009-01-20T00:00:00Z",
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                }
                            }
                        ]
                    },
                }
            ]
        },
        sitelinks={},
    )
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event() is True


def test_entity_has_event_false_no_position(mock_query):
    """Test that entity_has_event returns False when the entity has no positions."""
    entity = Entity(
        id="Q1",
        type="item",
        pageid=123,
        ns=0,
        title="Q1",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Barack Obama")},
        descriptions={
            "en": Property(language="en", value="44th President of the United States")
        },
        aliases={"en": []},
        claims={},
        sitelinks={},
    )
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event() is False


def test_entity_has_event_false_no_start_time(mock_query):
    """Test that entity_has_event returns False when the position has no start time."""
    entity = Entity(
        id="Q1",
        type="item",
        pageid=123,
        ns=0,
        title="Q1",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Barack Obama")},
        descriptions={
            "en": Property(language="en", value="44th President of the United States")
        },
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q2"}},
                    }
                }
            ]
        },
        sitelinks={},
    )
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event() is False


def test_create_wiki_event_with_work_location(mock_query):
    """Test creating a wiki event for a position with a work location."""
    entity = Entity(
        id="Q1",
        type="item",
        pageid=123,
        ns=0,
        title="Q1",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Barack Obama")},
        descriptions={
            "en": Property(language="en", value="44th President of the United States")
        },
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q2"}},
                    },
                    "qualifiers": {
                        START_TIME: [
                            {
                                "hash": "hash1",
                                "snaktype": "value",
                                "property": START_TIME,
                                "datavalue": {
                                    "value": {
                                        "time": "+2009-01-20T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        REPLACES: [
                            {
                                "datavalue": {"value": {"id": "Q4"}},
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "On January 20, 2009, Barack Obama took the position of President of the United States at White House, replacing George W. Bush."
    )
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Barack Obama"
    assert event.people_tags[1].name == "George W. Bush"
    assert event.place_tag.name == "White House"
    assert event.time_tag.name == "January 20, 2009"


def test_create_wiki_event_with_jurisdiction(mock_query):
    """Test creating a wiki event for a position with a jurisdiction."""
    entity = Entity(
        id="Q8",
        type="item",
        pageid=123,
        ns=0,
        title="Q8",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Arnold Schwarzenegger")},
        descriptions={"en": Property(language="en", value="Actor and politician")},
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q5"}},
                    },
                    "qualifiers": {
                        START_TIME: [
                            {
                                "hash": "hash1",
                                "snaktype": "value",
                                "property": START_TIME,
                                "datavalue": {
                                    "value": {
                                        "time": "+2003-11-17T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    }
                                },
                            }
                        ],
                        REPLACES: [
                            {
                                "datavalue": {"value": {"id": "Q9"}},
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "On November 17, 2003, Arnold Schwarzenegger took the position of Governor of California at California State Capitol, replacing Gray Davis."
    )
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Arnold Schwarzenegger"
    assert event.people_tags[1].name == "Gray Davis"
    assert event.place_tag.name == "California State Capitol"
    assert event.time_tag.name == "November 17, 2003"


def test_create_wiki_event_with_represents(mock_query):
    """Test creating a wiki event for a position with a represents relationship."""
    entity = Entity(
        id="Q13",
        type="item",
        pageid=123,
        ns=0,
        title="Q13",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Michael Bloomberg")},
        descriptions={
            "en": Property(language="en", value="Businessman and politician")
        },
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q10"}},
                    },
                    "qualifiers": {
                        START_TIME: [
                            {
                                "hash": "hash1",
                                "snaktype": "value",
                                "property": START_TIME,
                                "datavalue": {
                                    "value": {
                                        "time": "+2002-01-01T00:00:00Z",
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
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "On January 1, 2002, Michael Bloomberg took the position of Mayor of New York City at City Hall."
    )
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Michael Bloomberg"
    assert event.place_tag.name == "City Hall"
    assert event.time_tag.name == "January 1, 2002"


def test_create_wiki_event_no_location(mock_query):
    """Test that no event is created when no location can be found."""
    entity = Entity(
        id="Q1",
        type="item",
        pageid=123,
        ns=0,
        title="Q1",
        lastrevid=456,
        modified="2024-04-01T00:00:00Z",
        labels={"en": Property(language="en", value="Test Person")},
        descriptions={"en": Property(language="en", value="Test description")},
        aliases={"en": []},
        claims={
            POSITION_HELD: [
                {
                    "mainsnak": {
                        "datavalue": {"value": {"id": "Q999"}},  # Unknown position
                    },
                    "qualifiers": {
                        START_TIME: [
                            {
                                "hash": "hash1",
                                "snaktype": "value",
                                "property": START_TIME,
                                "datavalue": {
                                    "value": {
                                        "time": "+2000-01-01T00:00:00Z",
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
    factory = PersonTookPosition(entity=entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError, match="No valid position events found"):
        factory.create_wiki_event()
