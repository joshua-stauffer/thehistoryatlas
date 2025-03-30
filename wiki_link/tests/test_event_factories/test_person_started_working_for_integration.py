import os
import json
import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.person_started_working_for import (
    PersonStartedWorkingFor,
)
from wiki_service.wikidata_query_service import WikiDataQueryService


@pytest.fixture
def config(monkeypatch):
    monkeypatch.setenv("WIKILINK_CONTACT", "test@example.com")
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_einstein_employment_events(service):
    """
    Integration test using Albert Einstein's employment data.
    Einstein was a professor at ETH Zurich (Q11942) and other institutions.
    """
    EINSTEIN_ID = "Q937"
    entity = service.get_entity(id=EINSTEIN_ID)
    factory = PersonStartedWorkingFor(entity=entity, query=service)

    # Verify that Einstein has employment events
    assert factory.entity_has_event()

    # Debug: Print the first employer claim's time qualifier
    employer_claim = entity.claims["P108"][0]
    time_claim = employer_claim["qualifiers"]["P580"][0]
    print("\nTime claim structure:")
    print(json.dumps(time_claim, indent=2))

    # Get the events
    wiki_events = factory.create_wiki_event()

    # Verify we got some events
    assert len(wiki_events) > 0

    # Verify each event has the required fields
    for event in wiki_events:
        # Check summary
        assert isinstance(event.summary, str)
        assert "Einstein" in event.summary
        assert "started working" in event.summary

        # Check people tags
        assert len(event.people_tags) == 1
        person_tag = event.people_tags[0]
        assert person_tag.name == "Albert Einstein"
        assert person_tag.wiki_id == EINSTEIN_ID

        # Check place tag (may be None if location not found)
        if event.place_tag:
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
        assert event.time_tag.time_definition.precision in (
            9,
            10,
            11,
        )  # year, month, or day precision
