import os
import json
import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.person_left_position import PersonLeftPosition
from wiki_service.wikidata_query_service import WikiDataQueryService


@pytest.fixture
def config():
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_barack_obama_position_events(service):
    """
    Integration test using Barack Obama's position data.
    Barack Obama (Q76) left several positions including:
    - President of the United States
    - US Senator from Illinois
    - Illinois State Senator
    """
    BARACK_OBAMA_ID = "Q76"
    entity = service.get_entity(id=BARACK_OBAMA_ID)
    factory = PersonLeftPosition(entity=entity, query=service, entity_type="PERSON")

    # Verify that Barack Obama has position events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()

    # Verify we got at least one event
    assert len(wiki_events) >= 1

    # Expected event for verification (at least one of these should match)
    expected_events = [
        "Barack Obama left the position of President of the United States at White House",
        "Barack Obama left the position of member of the State Senate of Illinois",
        "Barack Obama left the position of United States senator in Illinois Class 3 senate seat",
        "Barack Obama left the position of President-elect of the United States",
    ]

    # Verify at least one of our expected events is found
    found_match = False
    for event in wiki_events:
        for expected in expected_events:
            if expected in event.summary:
                found_match = True
                break
        if found_match:
            break

    assert (
        found_match
    ), f"None of the expected events were found in {[e.summary for e in wiki_events]}"

    # Check a specific event (the presidency is the most reliable one)
    president_event = None
    for event in wiki_events:
        if (
            "President of the United States" in event.summary
            and "2017" in event.summary
        ):
            president_event = event
            break

    if president_event:
        # Check people tags
        assert len(president_event.people_tags) >= 1  # At least Barack Obama
        person_tag = president_event.people_tags[0]
        assert person_tag.name == "Barack Obama"
        assert person_tag.wiki_id == BARACK_OBAMA_ID

        # Check place tag
        assert president_event.place_tag is not None
        assert president_event.place_tag.name
        assert president_event.place_tag.wiki_id
        assert president_event.place_tag.location is not None
        assert (
            president_event.place_tag.location.coordinates is not None
            or president_event.place_tag.location.geoshape is not None
        )

        # Check time tag
        assert president_event.time_tag is not None
        assert president_event.time_tag.name
        assert president_event.time_tag.time_definition is not None
        assert president_event.time_tag.time_definition.time
        # Day precision for end of presidency
        assert president_event.time_tag.time_definition.precision == 11
