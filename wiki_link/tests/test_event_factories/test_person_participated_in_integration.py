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
