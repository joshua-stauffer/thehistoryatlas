import os
import json
import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.person_stopped_working_for import (
    PersonStoppedWorkingFor,
)
from wiki_service.wikidata_query_service import WikiDataQueryService


@pytest.fixture
def config():
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_einstein_employment_events(service):
    """
    Integration test using Albert Einstein's employment data.
    Einstein worked at ETH Zurich (Q11942) and other institutions.
    """
    EINSTEIN_ID = "Q937"
    entity = service.get_entity(id=EINSTEIN_ID)
    factory = PersonStoppedWorkingFor(
        entity=entity, query=service, entity_type="PERSON"
    )

    # Verify that Einstein has employment events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()

    # Verify we got some events
    assert len(wiki_events) > 0

    # Verify each event has the required fields
    for event in wiki_events:
        # Check summary
        assert isinstance(event.summary, str)
        assert "Einstein" in event.summary
        assert "stopped working" in event.summary

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
