import os
import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.book_was_published import BookWasPublished
from wiki_service.wikidata_query_service import WikiDataQueryService


@pytest.fixture
def config():
    return WikiServiceConfig()


@pytest.fixture
def service(config):
    return WikiDataQueryService(config=config)


def test_nineteen_eighty_four_book_published(service):
    """
    Integration test using George Orwell's 1984 book data.
    It was published in the UK in 1949 by Secker & Warburg.
    """
    NINETEEN_EIGHTY_FOUR_ID = "Q208460"
    entity = service.get_entity(id=NINETEEN_EIGHTY_FOUR_ID)
    factory = BookWasPublished(entity=entity, query=service, entity_type="BOOK")

    # Verify that 1984 has the required events
    assert factory.entity_has_event()

    # Get the events
    wiki_events = factory.create_wiki_event()

    # Verify we got at least one event
    assert len(wiki_events) >= 1

    # Check the content of the first event
    event = wiki_events[0]

    # The summary should mention George Orwell and 1984
    assert "George Orwell" in event.summary
    assert "Nineteen Eighty-Four" in event.summary or "1984" in event.summary
    assert "1949" in event.summary
    assert "United Kingdom" in event.summary

    # Check people tags
    assert len(event.people_tags) >= 1  # At least George Orwell
    person_tag = event.people_tags[0]
    assert person_tag.name == "George Orwell"
    assert person_tag.wiki_id is not None

    # Check place tag
    assert event.place_tag is not None
    assert event.place_tag.name == "United Kingdom"
    assert event.place_tag.wiki_id is not None
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
    assert event.time_tag.time_definition.precision == 9  # Year precision for 1949
