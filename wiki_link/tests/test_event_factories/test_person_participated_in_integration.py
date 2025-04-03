import os
import json
import pytest
from unittest.mock import patch, MagicMock

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.person_participated_in import PersonParticipatedIn
from wiki_service.wikidata_query_service import WikiDataQueryService
from wiki_service.types import GeoLocation, CoordinateLocation


@pytest.fixture
def config():
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_barack_obama_participation_events(service):
    """
    Integration test using Barack Obama's participation data.
    Barack Obama (Q76) participated in several events including:
    - Presidential elections
    - Nobel Peace Prize ceremony
    - Various summits and diplomatic meetings
    """
    BARACK_OBAMA_ID = "Q76"
    entity = service.get_entity(id=BARACK_OBAMA_ID)
    factory = PersonParticipatedIn(entity=entity, query=service, entity_type="PERSON")

    # Verify that Barack Obama has participation events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()
    for event in wiki_events:
        print(event.summary)

    # Verify we got events
    assert len(wiki_events) > 0

    # Check some expected events (exact events may vary based on Wikidata)
    # Example summaries that might be included
    expected_keywords = [
        "Obama",
        "participated",
        "ceremony",
        "election",
        "summit",
    ]

    # Verify at least one event contains some of our expected keywords
    found_match = False
    for event in wiki_events:
        if any(
            keyword.lower() in event.summary.lower() for keyword in expected_keywords
        ):
            found_match = True
            break

    assert found_match, "No event with expected keywords found"

    # Test structure of events
    for event in wiki_events:
        # Check people tags
        assert len(event.people_tags) >= 1  # At least Barack Obama
        person_tag = event.people_tags[0]
        assert person_tag.name == "Barack Obama"
        assert person_tag.wiki_id == BARACK_OBAMA_ID

        # Check place tag
        assert event.place_tag is not None
        assert event.place_tag.name
        assert event.place_tag.wiki_id
        assert event.place_tag.location is not None
        assert (
            event.place_tag.location.coordinates is not None
            or event.place_tag.location.geoshape is not None
        )

        # Check time tag
        assert event.time_tag is not None
        assert event.time_tag.name
        assert event.time_tag.time_definition is not None
        assert event.time_tag.time_definition.time
        assert event.time_tag.time_definition.precision in [
            9,
            10,
            11,
        ]  # year, month, or day precision


def test_progressive_location_search():
    """Test the progressive location search through mocks to verify the behavior"""

    # Mock the configuration and query service
    mock_config = MagicMock()
    mock_query = MagicMock()

    # Mock entities
    mock_person = MagicMock()
    mock_person.id = "Q123"
    mock_person.labels = {"en": MagicMock(value="Test Person")}
    mock_person.claims = {"P1344": []}

    # Create a mock claim with POINT_IN_TIME qualifier but no location
    mock_claim = {
        "mainsnak": {"datavalue": {"value": {"id": "Q456"}}},  # Event ID
        "qualifiers": {
            "P585": [  # POINT_IN_TIME
                {
                    "datavalue": {
                        "value": {
                            "time": "+2022-01-01T00:00:00Z",
                            "timezone": 0,
                            "before": 0,
                            "after": 0,
                            "precision": 11,
                            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                        }
                    },
                    "hash": "hash123",
                    "property": "P585",
                    "snaktype": "value",
                }
            ]
        },
    }

    # Add the claim to the person
    mock_person.claims["P1344"].append(mock_claim)

    # Mock the event entity
    mock_event = MagicMock()
    mock_event.id = "Q456"
    mock_event.claims = {}

    # Mock the organizer entity
    mock_organizer = MagicMock()
    mock_organizer.id = "Q789"
    mock_organizer.claims = {
        "P17": [  # COUNTRY
            {"mainsnak": {"datavalue": {"value": {"id": "Q30"}}}}  # United States
        ]
    }

    # Setup the mock event with an organizer
    mock_event.claims["P664"] = [  # ORGANIZER
        {"mainsnak": {"datavalue": {"value": {"id": "Q789"}}}}  # Organizer ID
    ]

    # Configure the mock query service
    mock_query.get_entity.side_effect = lambda id: {
        "Q123": mock_person,
        "Q456": mock_event,
        "Q789": mock_organizer,
    }.get(id)

    mock_query.get_label.side_effect = lambda id, language: {
        "Q123": "Test Person",
        "Q456": "Test Event",
        "Q789": "Test Organizer",
        "Q30": "United States",
    }.get(id)

    # Mock a properly formed coordinate location and geo location
    mock_coordinate = CoordinateLocation(
        id="test-id",
        rank="normal",
        type="statement",
        snaktype="value",
        property="P625",
        hash="test-hash",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=0,
        precision=0.1,
        globe="http://www.wikidata.org/entity/Q2",
    )

    mock_geo = GeoLocation(coordinates=mock_coordinate, geoshape=None)

    mock_query.get_geo_location.return_value = mock_geo

    # Initialize the factory with mocks
    factory = PersonParticipatedIn(
        entity=mock_person, query=mock_query, entity_type="PERSON"
    )

    # Verify it has events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()

    # We should get one event
    assert len(wiki_events) == 1

    # Verify the event has the correct structure
    event = wiki_events[0]
    assert "Test Person" in event.summary
    assert "Test Event" in event.summary

    # Verify the location is from the organizer's country
    assert event.place_tag is not None
    assert "United States" in event.place_tag.name

    # Verify the time tag is correct
    assert event.time_tag is not None
    assert event.time_tag.time_definition.precision == 11  # day precision
