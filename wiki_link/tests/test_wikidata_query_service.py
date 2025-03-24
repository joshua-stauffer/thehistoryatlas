import pytest
import os
from unittest.mock import patch, MagicMock

from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    CoordinateLocation,
    GeoshapeLocation,
    TimeDefinition,
    Property,
)
from wiki_service.types import WikiDataItem
from wiki_service.config import WikiServiceConfig

# Mock responses for our tests
MOCK_SPARQL_RESPONSE = {
    "head": {"vars": ["item"]},
    "results": {
        "bindings": [
            {"item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q1"}},
            {"item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q2"}},
        ]
    },
}

MOCK_PEOPLE_RESPONSE = {
    "head": {"vars": ["item", "itemLabel"]},
    "results": {
        "bindings": [
            {
                "item": {
                    "type": "uri",
                    "value": f"http://www.wikidata.org/entity/Q{i}",
                },
                "itemLabel": {"type": "literal", "value": f"Person {i}"},
            }
            for i in range(1, 101)
        ]
    },
}

MOCK_COUNT_RESPONSE = {
    "head": {"vars": ["count"]},
    "results": {"bindings": [{"count": {"type": "literal", "value": "12000000"}}]},
}


def test_query_person(config):
    EINSTEIN = "Q937"
    service = WikiDataQueryService(config)
    person = service.get_entity(id=EINSTEIN)
    for lang, prop in person.descriptions.items():
        assert isinstance(prop, Property)
    for lang, prop in person.labels.items():
        assert isinstance(prop, Property)
    for key, prop_list in person.aliases.items():
        assert all([isinstance(prop, Property) for prop in prop_list])


def test_query_point(config):
    ROME_ID = "Q220"
    service = WikiDataQueryService(config)
    place = service.get_entity(id=ROME_ID)
    coords = service.get_coordinate_location(place)
    assert isinstance(place, Entity)
    assert isinstance(coords, CoordinateLocation)


def test_query_geoshape(config):
    ITALY_ID = "Q38"
    service = WikiDataQueryService(config)
    place = service.get_entity(id=ITALY_ID)
    geoshape = service.get_geoshape_location(place)
    assert isinstance(place, Entity)
    assert isinstance(geoshape, GeoshapeLocation)


def test_query_time(config):
    BACHS_BIRTHDAY = "Q69125225"
    service = WikiDataQueryService(config)
    time = service.get_entity(id=BACHS_BIRTHDAY)
    time_detail = service.get_time(entity=time)
    assert isinstance(time, Entity)
    assert isinstance(time_detail, TimeDefinition)


@patch("wiki_service.wikidata_query_service.SPARQLWrapper.query")
def test_make_sparql_query(mock_query, config):
    mock_result = MagicMock()
    mock_result.convert.return_value = MOCK_SPARQL_RESPONSE
    mock_query.return_value = mock_result

    service = WikiDataQueryService(config)
    url = "https://query.wikidata.org/sparql"
    query = """
    SELECT ?item
    WHERE 
    {
      ?item wdt:P31 wd:Q5 .
    }
    LIMIT 10
    """
    result = service.make_sparql_query(query=query, url=url)
    assert isinstance(result, dict)
    assert "bindings" in result
    assert len(result["bindings"]) == 2
    assert all("item" in item for item in result["bindings"])


def test_get_qid_from_uri(config):
    service = WikiDataQueryService(config)
    uri = "http://www.wikidata.org/entity/Q23"

    res = service.get_qid_from_uri(uri)
    assert res == "Q23"


@patch("wiki_service.wikidata_query_service.SPARQLWrapper.query")
def test_find_people(mock_query, config):
    mock_result = MagicMock()
    mock_result.convert.return_value = MOCK_PEOPLE_RESPONSE
    mock_query.return_value = mock_result

    service = WikiDataQueryService(config)
    people = service.find_people(limit=100, offset=0)
    assert len(people) == 100
    for person in people:
        assert isinstance(person, WikiDataItem)


@patch("wiki_service.wikidata_query_service.SPARQLWrapper.query")
def test_get_wikidata_people_count(mock_query, config):
    mock_result = MagicMock()
    mock_result.convert.return_value = MOCK_COUNT_RESPONSE
    mock_query.return_value = mock_result

    service = WikiDataQueryService(config=config)
    count = service.get_wikidata_people_count()
    assert isinstance(count, int)
    assert count == 12000000


def test_get_label(config):
    service = WikiDataQueryService(config)

    label = service.get_label(id="Q1339", language="en")
    assert label == "Johann Sebastian Bach"


def test_non_ascii_labels():
    """Test that labels with non-ASCII characters are handled correctly"""
    # Create a mock entity dictionary with non-ASCII characters
    entity_dict = {
        "id": "Q123",
        "pageid": 123,
        "ns": 0,
        "title": "Test",
        "lastrevid": 1234,
        "modified": "2024-03-20T00:00:00Z",
        "type": "item",
        "labels": {
            "es": {"language": "es", "value": "María Ruiz-Tagle"},
            "ja": {"language": "ja", "value": "日本語"},
        },
        "descriptions": {},
        "aliases": {},
        "claims": {},
        "sitelinks": {},
    }

    # Test the static method directly without needing a service instance
    entity = WikiDataQueryService.build_entity(entity_dict)

    # Verify that non-ASCII characters are preserved correctly
    assert entity.labels["es"].value == "María Ruiz-Tagle"
    assert entity.labels["ja"].value == "日本語"


def test_non_ascii_labels_live_api(monkeypatch):
    """Test that labels with non-ASCII characters are handled correctly when fetching from the live API"""
    # Set up minimal environment for config
    monkeypatch.setenv("THA_DB_URI", "")

    # Q8605 is Simón Bolívar, a well-known historical figure with non-ASCII characters
    service = WikiDataQueryService(WikiServiceConfig())
    entity = service.get_entity(id="Q8605")

    # Verify that Spanish name contains correct non-ASCII characters
    assert "Simón" in entity.labels["es"].value
    assert "Bolívar" in entity.labels["es"].value


def test_non_ascii_labels_unicode_escapes():
    """Test that labels with Unicode escape sequences are handled correctly"""
    # Create a mock entity dictionary with Unicode escape sequences
    entity_dict = {
        "id": "Q123",
        "pageid": 123,
        "ns": 0,
        "title": "Test",
        "lastrevid": 1234,
        "modified": "2024-03-20T00:00:00Z",
        "type": "item",
        "labels": {
            "es": {
                "language": "es",
                "value": "Mar\u00eda Ruiz-Tagle",  # This is how it appears in your system
            }
        },
        "descriptions": {},
        "aliases": {},
        "claims": {},
        "sitelinks": {},
    }

    entity = WikiDataQueryService.build_entity(entity_dict)

    # Verify that the Unicode escape sequence is properly converted to the actual character
    assert entity.labels["es"].value == "María Ruiz-Tagle"
