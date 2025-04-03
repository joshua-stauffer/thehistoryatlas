import pytest
import os
from unittest.mock import patch, MagicMock, Mock
import responses
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    WikiDataQueryServiceError,
)
from wiki_service.types import (
    CoordinateLocation,
    Entity,
    GeoLocation,
    GeoshapeLocation,
    Property,
    TimeDefinition,
)
from wiki_service.types import WikiDataItem
from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.q_numbers import (
    COORDINATE_LOCATION,
    LOCATION,
    COUNTRY,
)

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
    assert "results" in result
    assert "bindings" in result["results"]
    assert len(result["results"]["bindings"]) == 2
    assert all("item" in item for item in result["results"]["bindings"])


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


def test_get_description(config):
    """Test retrieving a description for an entity that has one"""
    service = WikiDataQueryService(config)

    # Q1339 is Johann Sebastian Bach
    description = service.get_description(id="Q1339", language="en")
    assert description is not None
    assert "composer" in description.lower()


def test_get_description_missing(config):
    """Test retrieving a description for an entity/language combination that doesn't exist"""
    service = WikiDataQueryService(config)

    # Using a made-up ID that shouldn't exist
    description = service.get_description(id="Q999999999", language="en")
    assert description is None


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


# Rate limiting tests
@responses.activate
def test_get_entity_rate_limit_retry_success(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Mock a 429 response with retry-after header
    responses.add(
        responses.GET,
        url,
        status=429,
        headers={"retry-after": "1"},
    )

    # Mock a successful response after retry
    mock_response = {
        "entities": {
            "Q42": {
                "id": "Q42",
                "pageid": 123,
                "ns": 0,
                "title": "Test",
                "lastrevid": 456,
                "modified": "2024-01-01T00:00:00Z",
                "type": "item",
                "labels": {},
                "descriptions": {},
                "aliases": {},
                "claims": {},
                "sitelinks": {},
            }
        }
    }
    responses.add(responses.GET, url, json=mock_response, status=200)

    service = WikiDataQueryService(config)
    with patch("time.sleep") as mock_sleep:
        result = service.get_entity(entity_id)
        assert mock_sleep.call_args[0][0] == 1  # Verify sleep was called with 1 second
        assert result.id == "Q42"


@responses.activate
def test_get_entity_rate_limit_max_retries(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Add 6 rate limit responses (1 initial + 5 retries)
    for _ in range(6):
        responses.add(
            responses.GET,
            url,
            status=429,
            headers={"retry-after": "1"},
        )

    service = WikiDataQueryService(config)
    with patch("time.sleep"), pytest.raises(WikiDataQueryServiceError) as exc_info:
        service.get_entity(entity_id)
    assert "Maximum retries exceeded" in str(exc_info.value)


@responses.activate
def test_get_entity_rate_limit_no_retry_after(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Mock a 429 response without retry-after header
    responses.add(
        responses.GET,
        url,
        status=429,
    )

    service = WikiDataQueryService(config)
    with pytest.raises(WikiDataQueryServiceError) as exc_info:
        service.get_entity(entity_id)
    assert "Rate limit exceeded with no retry-after header" in str(exc_info.value)


@responses.activate
def test_get_label_rate_limit_retry_success(config):
    entity_id = "Q42"
    language = "en"
    url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{entity_id}/labels/{language}"

    # Mock a 429 response with retry-after header
    responses.add(
        responses.GET,
        url,
        status=429,
        headers={"retry-after": "1"},
    )

    # Mock a successful response after retry
    responses.add(responses.GET, url, body='"Test Label"', status=200)

    service = WikiDataQueryService(config)
    with patch("time.sleep") as mock_sleep:
        result = service.get_label(entity_id, language)
        assert mock_sleep.call_args[0][0] == 1
        assert result == "Test Label"


@responses.activate
def test_sparql_query_rate_limit_retry_success(config):
    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
    url = "https://query.wikidata.org/sparql"

    mock_response = {"results": {"bindings": [{"s": {"value": "test"}}]}}

    # Mock SPARQLWrapper to simulate rate limiting
    with patch("wiki_service.wikidata_query_service.SPARQLWrapper.query") as mock_query:
        # First call raises HTTPError with 429
        error_response = Mock()
        error_response.headers = {"retry-after": "1"}
        error_response.status_code = 429
        http_error = HTTPError(url, 429, "Too Many Requests", {}, None)
        http_error.response = error_response

        # Second call succeeds
        success_response = Mock()
        success_response.convert.return_value = mock_response

        mock_query.side_effect = [http_error, success_response]

        service = WikiDataQueryService(config)
        with patch("time.sleep") as mock_sleep:
            result = service.make_sparql_query(query, url)

        # Verify retry behavior
        assert mock_query.call_count == 2
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args[0][0] == 1.0
        assert result == mock_response


@responses.activate
def test_get_entity_rate_limit_retry_success_with_date(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Create a fixed test time
    test_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    future_date = test_time + timedelta(seconds=2)
    retry_after_date = future_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Mock a 429 response with retry-after header as date
    responses.add(
        responses.GET,
        url,
        status=429,
        headers={"retry-after": retry_after_date},
    )

    # Mock a successful response after retry
    mock_response = {
        "entities": {
            "Q42": {
                "id": "Q42",
                "pageid": 123,
                "ns": 0,
                "title": "Test",
                "lastrevid": 456,
                "modified": "2024-01-01T00:00:00Z",
                "type": "item",
                "labels": {},
                "descriptions": {},
                "aliases": {},
                "claims": {},
                "sitelinks": {},
            }
        }
    }
    responses.add(responses.GET, url, json=mock_response, status=200)

    service = WikiDataQueryService(config)
    with patch.object(
        WikiDataQueryService, "_get_current_time", return_value=test_time
    ), patch("time.sleep") as mock_sleep:
        result = service.get_entity(entity_id)
        # Verify sleep was called with 2 seconds
        assert mock_sleep.call_args[0][0] == 2.0
        assert result.id == "Q42"


@responses.activate
def test_get_entity_rate_limit_invalid_retry_after(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Mock a 429 response with invalid retry-after header
    responses.add(
        responses.GET,
        url,
        status=429,
        headers={"retry-after": "invalid-format"},
    )

    service = WikiDataQueryService(config)
    with pytest.raises(WikiDataQueryServiceError) as exc_info:
        service.get_entity(entity_id)
    assert "Invalid retry-after format" in str(exc_info.value)


@responses.activate
def test_get_entity_rate_limit_past_date(config):
    entity_id = "Q42"
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"

    # Create a fixed test time
    test_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    past_date = test_time - timedelta(seconds=60)
    retry_after_date = past_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Mock a 429 response with retry-after header as past date
    responses.add(
        responses.GET,
        url,
        status=429,
        headers={"retry-after": retry_after_date},
    )

    # Mock a successful response after retry
    mock_response = {
        "entities": {
            "Q42": {
                "id": "Q42",
                "pageid": 123,
                "ns": 0,
                "title": "Test",
                "lastrevid": 456,
                "modified": "2024-01-01T00:00:00Z",
                "type": "item",
                "labels": {},
                "descriptions": {},
                "aliases": {},
                "claims": {},
                "sitelinks": {},
            }
        }
    }
    responses.add(responses.GET, url, json=mock_response, status=200)

    service = WikiDataQueryService(config)
    with patch.object(
        WikiDataQueryService, "_get_current_time", return_value=test_time
    ), patch("time.sleep") as mock_sleep:
        result = service.get_entity(entity_id)
        # Verify sleep was called with 0 seconds for past dates
        assert mock_sleep.call_args[0][0] == 0
        assert result.id == "Q42"


@pytest.fixture
def mock_config():
    config = Mock()
    config.contact = "test@example.com"
    return config


@pytest.fixture
def service(mock_config):
    return WikiDataQueryService(config=mock_config)


@pytest.fixture
def entity_with_coordinate():
    return Entity(
        id="Q123",
        pageid=1,
        ns=0,
        title="Test Entity",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Entity")},
        descriptions={},
        aliases={},
        claims={
            COORDINATE_LOCATION: [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": COORDINATE_LOCATION,
                        "hash": "test_hash",
                        "datavalue": {
                            "value": {
                                "latitude": 51.5074,
                                "longitude": -0.1278,
                                "altitude": None,
                                "precision": 0.0001,
                                "globe": "http://www.wikidata.org/entity/Q2",
                            },
                            "type": "globecoordinate",
                        },
                    },
                    "type": "statement",
                    "id": "Q123$test",
                    "rank": "normal",
                }
            ]
        },
        sitelinks={},
    )


@pytest.fixture
def entity_with_location():
    return Entity(
        id="Q456",
        pageid=1,
        ns=0,
        title="Test Entity",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Entity")},
        descriptions={},
        aliases={},
        claims={LOCATION: [{"mainsnak": {"datavalue": {"value": {"id": "Q789"}}}}]},
        sitelinks={},
    )


@pytest.fixture
def entity_with_country():
    return Entity(
        id="Q456",
        pageid=1,
        ns=0,
        title="Test Entity",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Entity")},
        descriptions={},
        aliases={},
        claims={COUNTRY: [{"mainsnak": {"datavalue": {"value": {"id": "Q789"}}}}]},
        sitelinks={},
    )


@pytest.fixture
def entity_without_location():
    return Entity(
        id="Q456",
        pageid=1,
        ns=0,
        title="Test Entity",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Entity")},
        descriptions={},
        aliases={},
        claims={},
        sitelinks={},
    )


def test_get_hierarchical_location_with_coordinate(service, entity_with_coordinate):
    """Test that coordinate location is returned when available"""
    location = service.get_hierarchical_location(entity_with_coordinate)
    assert location is not None
    assert location.coordinates is not None
    assert location.coordinates.latitude == 51.5074
    assert location.coordinates.longitude == -0.1278


def test_get_hierarchical_location_with_location(
    service, entity_with_location, mock_location_entity
):
    """Test that location property is resolved to coordinates when available"""
    service.get_entity = Mock(return_value=mock_location_entity)
    location = service.get_hierarchical_location(entity_with_location)
    assert location is not None
    assert location.coordinates is not None
    service.get_entity.assert_called_with("Q789")


def test_get_hierarchical_location_with_country(
    service, entity_with_country, mock_country_entity
):
    """Test that country property is resolved to coordinates when available"""
    service.get_entity = Mock(return_value=mock_country_entity)
    location = service.get_hierarchical_location(entity_with_country)
    assert location is not None
    assert location.coordinates is not None
    service.get_entity.assert_called_with("Q789")


def test_get_hierarchical_location_without_location(service, entity_without_location):
    """Test that None is returned when no location information is available"""
    location = service.get_hierarchical_location(entity_without_location)
    assert location.coordinates is None


@pytest.fixture
def mock_location_entity():
    """Mock entity returned when looking up a location reference"""
    return Entity(
        id="Q789",
        pageid=1,
        ns=0,
        title="Test Location",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Location")},
        descriptions={},
        aliases={},
        claims={
            COORDINATE_LOCATION: [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": COORDINATE_LOCATION,
                        "hash": "test_hash",
                        "datavalue": {
                            "value": {
                                "latitude": 51.5074,
                                "longitude": -0.1278,
                                "altitude": None,
                                "precision": 0.0001,
                                "globe": "http://www.wikidata.org/entity/Q2",
                            },
                            "type": "globecoordinate",
                        },
                    },
                    "type": "statement",
                    "id": "Q789$test",
                    "rank": "normal",
                }
            ]
        },
        sitelinks={},
    )


@pytest.fixture
def mock_country_entity():
    """Mock entity returned when looking up a country reference"""
    return Entity(
        id="Q789",
        pageid=1,
        ns=0,
        title="Test Country",
        lastrevid=1,
        modified="2024-03-21T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="Test Country")},
        descriptions={},
        aliases={},
        claims={
            COORDINATE_LOCATION: [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": COORDINATE_LOCATION,
                        "hash": "test_hash",
                        "datavalue": {
                            "value": {
                                "latitude": 51.5074,
                                "longitude": -0.1278,
                                "altitude": None,
                                "precision": 0.0001,
                                "globe": "http://www.wikidata.org/entity/Q2",
                            },
                            "type": "globecoordinate",
                        },
                    },
                    "type": "statement",
                    "id": "Q789$test",
                    "rank": "normal",
                }
            ]
        },
        sitelinks={},
    )


@patch("wiki_service.wikidata_query_service.SPARQLWrapper.query")
def test_find_works_of_art(mock_query, config):
    mock_result = MagicMock()
    mock_result.convert.return_value = {
        "results": {
            "bindings": [
                {
                    "item": {
                        "value": "http://www.wikidata.org/entity/Q12345",
                    }
                },
                {
                    "item": {
                        "value": "http://www.wikidata.org/entity/Q67890",
                    }
                },
            ]
        }
    }
    mock_query.return_value = mock_result

    service = WikiDataQueryService(config)
    works = service.find_works_of_art(limit=100, offset=0)

    assert len(works) == 2
    expected_works = {
        WikiDataItem(url="http://www.wikidata.org/entity/Q12345", qid="Q12345"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q67890", qid="Q67890"),
    }
    assert works == expected_works


@pytest.fixture
def mock_entity_with_time_qualifiers():
    """Create a mock entity with time data in qualifiers"""
    return Entity(
        id="Q57125",
        pageid=57125,
        ns=0,
        title="Q57125",
        lastrevid=123,
        modified="2024-04-03T00:00:00Z",
        type="item",
        labels={},
        descriptions={},
        aliases={},
        sitelinks={},
        claims={
            "P1344": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "hash": "abc123",
                        "snaktype": "value",
                        "property": "P1344",
                        "datavalue": {
                            "value": {"id": "Q456", "entity-type": "item"},
                            "type": "wikibase-entityid",
                        },
                    },
                    "type": "statement",
                    "id": "Q57125$123",
                    "rank": "normal",
                    "qualifiers": {
                        "P585": [
                            {
                                "hash": "def456",
                                "snaktype": "value",
                                "property": "P585",
                                "datatype": "time",
                                "datavalue": {
                                    "value": {
                                        "time": "+1920-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    },
                                    "type": "time",
                                },
                            }
                        ],
                        "P580": [
                            {
                                "hash": "ghi789",
                                "snaktype": "value",
                                "property": "P580",
                                "datatype": "time",
                                "datavalue": {
                                    "value": {
                                        "time": "+1919-01-01T00:00:00Z",
                                        "timezone": 0,
                                        "before": 0,
                                        "after": 0,
                                        "precision": 11,
                                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    },
                                    "type": "time",
                                },
                            }
                        ],
                    },
                }
            ]
        },
    )


@pytest.fixture
def mock_entity_with_reference():
    """Create a mock entity with a reference to another entity"""
    return Entity(
        id="Q57125",
        pageid=57125,
        ns=0,
        title="Q57125",
        lastrevid=123,
        modified="2024-04-03T00:00:00Z",
        type="item",
        labels={},
        descriptions={},
        aliases={},
        sitelinks={},
        claims={
            "P1344": [
                {
                    "mainsnak": {
                        "datatype": "wikibase-item",
                        "hash": "abc123",
                        "snaktype": "value",
                        "property": "P1344",
                        "datavalue": {
                            "value": {"id": "Q789", "entity-type": "item"},
                            "type": "wikibase-entityid",
                        },
                    },
                    "type": "statement",
                    "id": "Q57125$123",
                    "rank": "normal",
                    "qualifiers": {},  # No time qualifiers here
                }
            ]
        },
    )


@pytest.fixture
def mock_referenced_entity():
    """Create a mock referenced entity with time data"""
    return Entity(
        id="Q789",
        pageid=789,
        ns=0,
        title="Q789",
        lastrevid=123,
        modified="2024-04-03T00:00:00Z",
        type="item",
        labels={},
        descriptions={},
        aliases={},
        sitelinks={},
        claims={
            "P585": [
                {
                    "mainsnak": {
                        "datatype": "time",
                        "hash": "def456",
                        "snaktype": "value",
                        "property": "P585",
                        "datavalue": {
                            "value": {
                                "time": "+1920-01-01T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                            "type": "time",
                        },
                    },
                    "type": "statement",
                    "id": "Q789$456",
                    "rank": "normal",
                }
            ]
        },
    )


def test_get_hierarchical_time_with_qualifiers(mock_entity_with_time_qualifiers):
    """Test getting time from qualifiers with priority order"""
    service = WikiDataQueryService(WikiServiceConfig())

    # Test getting P585 first (default)
    time_def = service.get_hierarchical_time(
        mock_entity_with_time_qualifiers, claim="P1344", time_props=["P585", "P580"]
    )
    assert time_def is not None
    assert time_def.time == "+1920-01-01T00:00:00Z"

    # Test getting P580 first when specified
    time_def = service.get_hierarchical_time(
        mock_entity_with_time_qualifiers, claim="P1344", time_props=["P580", "P585"]
    )
    assert time_def is not None
    assert time_def.time == "+1919-01-01T00:00:00Z"


def test_get_hierarchical_time_with_reference(
    mock_entity_with_reference, mock_referenced_entity
):
    """Test getting time from a referenced entity"""
    service = WikiDataQueryService(WikiServiceConfig())

    # Mock the get_entity call to return our referenced entity
    service.get_entity = Mock(return_value=mock_referenced_entity)

    time_def = service.get_hierarchical_time(
        mock_entity_with_reference, claim="P1344", time_props=["P585"]
    )

    # Verify the time was found in the referenced entity
    assert time_def is not None
    assert time_def.time == "+1920-01-01T00:00:00Z"

    # Verify get_entity was called with the correct ID
    service.get_entity.assert_called_once_with("Q789")


def test_get_hierarchical_time_reference_not_found(mock_entity_with_reference):
    """Test handling when referenced entity lookup fails"""
    service = WikiDataQueryService(WikiServiceConfig())

    # Mock get_entity to raise an exception
    service.get_entity = Mock(side_effect=Exception("Entity not found"))

    time_def = service.get_hierarchical_time(
        mock_entity_with_reference, claim="P1344", time_props=["P585"]
    )

    # Should return None when reference lookup fails
    assert time_def is None

    # Verify get_entity was called
    service.get_entity.assert_called_once_with("Q789")


def test_get_hierarchical_time_no_time():
    """Test when no time data is found"""
    service = WikiDataQueryService(WikiServiceConfig())

    # Create entity with no time data
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=123,
        modified="2024-04-03T00:00:00Z",
        type="item",
        labels={},
        descriptions={},
        aliases={},
        sitelinks={},
        claims={},
    )

    time_def = service.get_hierarchical_time(entity, claim="P1344")
    assert time_def is None


def test_get_hierarchical_time_invalid_claim():
    """Test with invalid/nonexistent claim"""
    service = WikiDataQueryService(WikiServiceConfig())

    # Create entity with some claims but not the one we're looking for
    entity = Entity(
        id="Q123",
        pageid=123,
        ns=0,
        title="Q123",
        lastrevid=123,
        modified="2024-04-03T00:00:00Z",
        type="item",
        labels={},
        descriptions={},
        aliases={},
        sitelinks={},
        claims={"P123": []},
    )

    time_def = service.get_hierarchical_time(entity, claim="P999")
    assert time_def is None
