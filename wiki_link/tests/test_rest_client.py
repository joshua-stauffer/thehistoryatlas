import pytest
from unittest.mock import Mock, patch
import requests
import json
from uuid import UUID

from wiki_service.rest_client import RestClient, RestClientError
from wiki_service.config import WikiServiceConfig


@pytest.fixture
def mock_session():
    with patch("requests.Session") as mock:
        session = Mock()
        mock.return_value = session
        # Mock successful authentication
        session.post.return_value.ok = True
        session.post.return_value.json.return_value = {"access_token": "test_token"}
        yield session


@pytest.fixture
def config():
    config = WikiServiceConfig()
    config.server_base_url = "test.example.com"
    config.username = "test_user"
    config.password = "test_pass"
    return config


def test_create_person_with_non_ascii_name(mock_session, config):
    """Test that non-ASCII characters in person names are handled correctly"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.json.return_value = {"id": "123"}

    # Try to create a person with non-ASCII characters
    name = "María Ruiz-Tagle"
    wikidata_id = "Q123"
    wikidata_url = "http://example.com/Q123"
    description = "A famous Chilean politician"

    result = client.create_person(
        name=name,
        wikidata_id=wikidata_id,
        wikidata_url=wikidata_url,
        description=description,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/wikidata/people"

    # Check that the data contains the correct non-ASCII characters
    data = call_args[1]["data"].decode("utf-8")
    assert "María" in data
    assert "Ruiz-Tagle" in data

    # Parse the JSON to verify structure
    json_data = json.loads(data)
    assert json_data["name"] == "María Ruiz-Tagle"
    assert json_data["wikidata_id"] == wikidata_id
    assert json_data["wikidata_url"] == wikidata_url
    assert json_data["description"] == description


def test_create_place_with_non_ascii_name(mock_session, config):
    """Test that non-ASCII characters in place names are handled correctly"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.json.return_value = {"id": "123"}

    # Try to create a place with non-ASCII characters
    name = "São Paulo"
    wikidata_id = "Q123"
    wikidata_url = "http://example.com/Q123"
    latitude = -23.5505
    longitude = -46.6333
    description = "The largest city in Brazil"

    result = client.create_place(
        name=name,
        wikidata_id=wikidata_id,
        wikidata_url=wikidata_url,
        latitude=latitude,
        longitude=longitude,
        description=description,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/wikidata/places"

    # Check that the data contains the correct non-ASCII characters
    data = call_args[1]["data"].decode("utf-8")
    assert "São" in data

    # Parse the JSON to verify structure
    json_data = json.loads(data)
    assert json_data["name"] == "São Paulo"
    assert json_data["wikidata_id"] == wikidata_id
    assert json_data["wikidata_url"] == wikidata_url
    assert json_data["latitude"] == latitude
    assert json_data["longitude"] == longitude
    assert json_data["description"] == description


def test_create_time_with_non_ascii_name(mock_session, config):
    """Test that non-ASCII characters in time names are handled correctly"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.json.return_value = {"id": "123"}

    # Try to create a time with non-ASCII characters
    name = "Día de la Independencia"
    wikidata_id = "Q123"
    wikidata_url = "http://example.com/Q123"
    date = "2024-03-19T00:00:00Z"
    calendar_model = "http://www.wikidata.org/entity/Q1985727"
    precision = 11

    result = client.create_time(
        name=name,
        wikidata_id=wikidata_id,
        wikidata_url=wikidata_url,
        date=date,
        calendar_model=calendar_model,
        precision=precision,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/wikidata/times"

    # Check that the data contains the correct non-ASCII characters
    data = call_args[1]["data"].decode("utf-8")
    assert "Día" in data

    # Parse the JSON to verify structure
    json_data = json.loads(data)
    assert json_data["name"] == "Día de la Independencia"
    assert json_data["wikidata_id"] == wikidata_id
    assert json_data["wikidata_url"] == wikidata_url
    assert json_data["date"] == date
    assert json_data["calendar_model"] == calendar_model
    assert json_data["precision"] == precision


def test_create_event_with_non_ascii_text(mock_session, config):
    """Test that non-ASCII characters in event data are handled correctly"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.json.return_value = {"id": "123"}

    # Try to create an event with non-ASCII characters
    summary = "José de San Martín cruzó los Andes"
    tags = [
        {"type": "PERSON", "name": "José de San Martín", "id": "Q123"},
        {"type": "PLACE", "name": "Los Andes", "id": "Q456"},
    ]
    citation = {
        "text": "Según la historia, José cruzó los Andes en 1817",
        "source": "Historia de América",
    }

    result = client.create_event(
        summary=summary, tags=tags, citation=citation, after=[]
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/wikidata/events"

    # Check that the data contains the correct non-ASCII characters
    data = call_args[1]["data"].decode("utf-8")
    assert "José" in data
    assert "cruzó" in data
    assert "Según" in data

    # Parse the JSON to verify structure
    json_data = json.loads(data)
    assert json_data["summary"] == summary
    assert json_data["tags"] == tags
    assert json_data["citation"] == citation


def test_create_person_error_handling(mock_session, config):
    """Test error handling when creating a person fails"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = False
    mock_session.post.return_value.text = "Error creating person"

    with pytest.raises(
        RestClientError, match="Failed to create person: Error creating person"
    ):
        client.create_person(
            name="Test Person",
            wikidata_id="Q123",
            wikidata_url="http://example.com/Q123",
        )


def test_check_time_exists_found(mock_session, config):
    """Test checking if a time exists when it does exist in the database"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True

    # Mock response with a UUID indicating time was found
    time_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_session.post.return_value.json.return_value = {"id": time_id}

    # Check if a time exists
    datetime = "2024-03-19T00:00:00Z"
    calendar_model = "http://www.wikidata.org/entity/Q1985727"
    precision = 11

    result = client.check_time_exists(
        datetime=datetime,
        calendar_model=calendar_model,
        precision=precision,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/times/exist"

    # Parse the JSON to verify structure
    data = json.loads(call_args[1]["data"].decode("utf-8"))
    assert data["datetime"] == datetime
    assert data["calendar_model"] == calendar_model
    assert data["precision"] == precision

    # Verify the result is the expected UUID
    assert isinstance(result, UUID)
    assert str(result) == time_id


def test_check_time_exists_not_found(mock_session, config):
    """Test checking if a time exists when it does not exist in the database"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True

    # Mock response with a null ID indicating time was not found
    mock_session.post.return_value.json.return_value = {"id": None}

    # Check if a time exists
    datetime = "2024-03-19T00:00:00Z"
    calendar_model = "http://www.wikidata.org/entity/Q1985727"
    precision = 11

    result = client.check_time_exists(
        datetime=datetime,
        calendar_model=calendar_model,
        precision=precision,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()

    # Verify the result is None
    assert result is None


def test_check_time_exists_error_handling(mock_session, config):
    """Test error handling when checking time existence fails"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = False
    mock_session.post.return_value.text = "Error checking time existence"

    # Try to check if a time exists, expect an error
    with pytest.raises(
        RestClientError,
        match="Failed to check time existence: Error checking time existence",
    ):
        client.check_time_exists(
            datetime="2024-03-19T00:00:00Z",
            calendar_model="http://www.wikidata.org/entity/Q1985727",
            precision=11,
        )


def test_create_time_with_description(mock_session, config):
    """Test creating a time tag with a description"""
    client = RestClient(config)

    # Reset the mock to clear the auth call
    mock_session.reset_mock()
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.json.return_value = {"id": "123"}

    # Create a time tag with a description
    name = "The Renaissance"
    wikidata_id = "Q123"
    wikidata_url = "http://example.com/Q123"
    date = "1400-01-01T00:00:00Z"
    calendar_model = "http://www.wikidata.org/entity/Q1985727"
    precision = 7
    description = "The period of European cultural rebirth"

    result = client.create_time(
        name=name,
        wikidata_id=wikidata_id,
        wikidata_url=wikidata_url,
        date=date,
        calendar_model=calendar_model,
        precision=precision,
        description=description,
    )

    # Verify the request was made with correct data
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args

    # Check that the URL is correct
    assert call_args[0][0] == "http://test.example.com/wikidata/times"

    # Parse the JSON to verify structure
    data = call_args[1]["data"].decode("utf-8")
    json_data = json.loads(data)
    assert json_data["name"] == name
    assert json_data["wikidata_id"] == wikidata_id
    assert json_data["wikidata_url"] == wikidata_url
    assert json_data["date"] == date
    assert json_data["calendar_model"] == calendar_model
    assert json_data["precision"] == precision
    assert json_data["description"] == description
