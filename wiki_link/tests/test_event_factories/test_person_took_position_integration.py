import os
import json
import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.person_took_position import PersonTookPosition
from wiki_service.wikidata_query_service import WikiDataQueryService


@pytest.fixture
def config():
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_lee_myung_bak_position_events(service):
    """
    Integration test using Lee Myung-bak's position data.
    Lee Myung-bak (Q14342) held several positions including:
    - President of South Korea
    - Mayor of Seoul
    - Member of the National Assembly
    """
    LEE_MYUNG_BAK_ID = "Q14342"
    entity = service.get_entity(id=LEE_MYUNG_BAK_ID)
    factory = PersonTookPosition(entity=entity, query=service, entity_type="PERSON")

    # Verify that Lee Myung-bak has position events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()

    # Verify we got the expected number of events
    assert len(wiki_events) == 3

    # Expected summaries for verification
    expected_summaries = [
        "On February 25, 2008, Lee Myung-bak took the position of President of South Korea, replacing Roh Moo-hyun.",
        "On July 1, 2002, Lee Myung-bak took the position of Mayor of Seoul.",
        "On May 30, 1996, Lee Myung-bak took the position of Member of the National Assembly of South Korea in Jongno, Seoul.",
    ]

    # Verify each event has the required fields and matches expected summaries
    actual_summaries = [event.summary for event in wiki_events]
    for expected in expected_summaries:
        assert expected in actual_summaries

    for event in wiki_events:
        # Check people tags
        assert len(event.people_tags) >= 1  # At least Lee Myung-bak
        person_tag = event.people_tags[0]
        assert person_tag.name == "Lee Myung-bak"
        assert person_tag.wiki_id == LEE_MYUNG_BAK_ID

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
        assert event.time_tag.time_definition.precision == 11  # day precision
