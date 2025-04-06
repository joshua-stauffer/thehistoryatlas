"""Tests for the OrationDelivered event factory."""

import pytest
from unittest.mock import MagicMock

from wiki_service.event_factories.oration_delivered import OrationDelivered
from wiki_service.types import (
    Entity,
    Property,
    GeoLocation,
    CoordinateLocation,
    TimeDefinition,
    LocationResult,
)
from wiki_service.event_factories.event_factory import UnprocessableEventError


@pytest.fixture
def mock_query():
    mock = MagicMock()
    mock.get_label.return_value = "Test Person"
    mock.get_entity.return_value = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Test Entity",
        lastrevid=1,
        modified="2024-01-01",
        type="item",
        labels={"en": Property(language="en", value="Test Entity")},
        descriptions={},
        aliases={},
        claims={},
        sitelinks={},
    )
    mock.get_time_definition_from_claim.return_value = TimeDefinition(
        id="Q123",
        rank="normal",
        type="statement",
        snaktype="value",
        property="P585",
        hash="hash",
        time="+1863-11-19T00:00:00Z",
        timezone=0,
        before=0,
        after=0,
        precision=11,
        calendarmodel="http://www.wikidata.org/entity/Q1985727",
    )
    mock.get_location_from_entity.return_value = LocationResult(
        name="Gettysburg",
        id="Q131178",
        geo_location=GeoLocation(
            coordinates=CoordinateLocation(
                id="Q131178",
                rank="normal",
                type="globecoordinate",
                snaktype="value",
                property="P625",
                hash="hash",
                latitude=39.8107,
                longitude=-77.2278,
                altitude=None,
                precision=0.0001,
                globe="http://www.wikidata.org/entity/Q2",
            ),
            geoshape=None,
        ),
    )
    return mock


@pytest.fixture
def mock_entity():
    return Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Test Oration",
        lastrevid=1,
        modified="2024-01-01",
        type="item",
        labels={"en": Property(language="en", value="Test Oration")},
        descriptions={},
        aliases={},
        claims={
            "P50": [  # AUTHOR
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P50",
                        "hash": "hash",
                        "datavalue": {
                            "type": "wikibase-entityid",
                            "value": {"id": "Q456"},
                        },
                    }
                }
            ],
            "P585": [  # POINT_IN_TIME
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P585",
                        "hash": "hash",
                        "datavalue": {
                            "type": "time",
                            "value": {
                                "time": "+1863-11-19T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    }
                }
            ],
            "P625": [  # COORDINATE_LOCATION
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P625",
                        "hash": "hash",
                        "datavalue": {
                            "type": "globecoordinate",
                            "value": {
                                "latitude": 39.8107,
                                "longitude": -77.2278,
                                "altitude": None,
                                "precision": 0.0001,
                                "globe": "http://www.wikidata.org/entity/Q2",
                            },
                        },
                    }
                }
            ],
        },
        sitelinks={},
    )


def test_entity_has_event_with_author(mock_query, mock_entity):
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    assert factory.entity_has_event() is True


def test_entity_has_event_with_speaker(mock_query):
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Test Oration",
        lastrevid=1,
        modified="2024-01-01",
        type="item",
        labels={"en": Property(language="en", value="Test Oration")},
        descriptions={},
        aliases={},
        claims={
            "P823": [  # SPEAKER
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P823",
                        "hash": "hash",
                        "datavalue": {
                            "type": "wikibase-entityid",
                            "value": {"id": "Q456"},
                        },
                    }
                }
            ],
            "P585": [  # POINT_IN_TIME
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P585",
                        "hash": "hash",
                        "datavalue": {
                            "type": "time",
                            "value": {
                                "time": "+1863-11-19T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        },
                    }
                }
            ],
        },
        sitelinks={},
    )
    factory = OrationDelivered(entity=entity, query=mock_query, entity_type="ORATION")
    assert factory.entity_has_event() is True


def test_entity_has_event_wrong_type(mock_query, mock_entity):
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    assert factory.entity_has_event() is False


def test_entity_has_event_missing_time(mock_query, mock_entity):
    mock_entity.claims.pop("P585")  # Remove POINT_IN_TIME
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    assert factory.entity_has_event() is False


def test_entity_has_event_missing_person(mock_query, mock_entity):
    mock_entity.claims.pop("P50")  # Remove AUTHOR
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    assert factory.entity_has_event() is False


def test_create_wiki_event(mock_query, mock_entity):
    mock_query.get_location_from_entity.return_value = LocationResult(
        name="Gettysburg",
        id="Q131178",
        geo_location=GeoLocation(
            coordinates=CoordinateLocation(
                id="Q131178",
                rank="normal",
                type="globecoordinate",
                snaktype="value",
                property="P625",
                hash="hash",
                latitude=39.8107,
                longitude=-77.2278,
                altitude=None,
                precision=0.0001,
                globe="http://www.wikidata.org/entity/Q2",
            ),
            geoshape=None,
        ),
    )

    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    events = factory.create_wiki_event()

    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "On November 19, 1863, Test Person delivered the speech Test Oration at Gettysburg."
    )
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Gettysburg"
    assert event.time_tag.name == "November 19, 1863"


def test_create_wiki_event_no_location(mock_query, mock_entity):
    mock_query.get_location_from_entity.return_value = None
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    with pytest.raises(UnprocessableEventError, match="No valid location found"):
        factory.create_wiki_event()


def test_create_wiki_event_no_time(mock_query, mock_entity):
    mock_entity.claims.pop("P585")  # Remove POINT_IN_TIME
    factory = OrationDelivered(
        entity=mock_entity, query=mock_query, entity_type="ORATION"
    )
    with pytest.raises(UnprocessableEventError):
        factory.create_wiki_event()
