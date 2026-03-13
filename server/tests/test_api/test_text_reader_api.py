"""Integration tests for text-reader and API key REST endpoints."""

import pytest
from uuid import uuid4, UUID
from typing import Dict

from fastapi.testclient import TestClient

from the_history_atlas.main import get_app


@pytest.fixture
def client(cleanup_db):
    return TestClient(get_app())


@pytest.fixture
def auth_headers(active_token: str, seed_accounts: None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {active_token}"}


# --- API Key Endpoints ---


class TestCreateApiKey:
    def test_returns_201(self, client, auth_headers):
        response = client.post(
            "/api-keys",
            json={"name": "test-key"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_raw_key(self, client, auth_headers):
        response = client.post(
            "/api-keys",
            json={"name": "test-key"},
            headers=auth_headers,
        )

        assert "raw_key" in response.json()

    def test_returns_name(self, client, auth_headers):
        response = client.post(
            "/api-keys",
            json={"name": "my-key"},
            headers=auth_headers,
        )

        assert response.json()["name"] == "my-key"

    def test_requires_jwt_auth(self, client):
        response = client.post("/api-keys", json={"name": "test-key"})

        assert response.status_code == 401


class TestDeactivateApiKey:
    def test_returns_success(self, client, auth_headers):
        create_response = client.post(
            "/api-keys",
            json={"name": "key-to-deactivate"},
            headers=auth_headers,
        )
        key_id = create_response.json()["id"]

        response = client.delete(f"/api-keys/{key_id}", headers=auth_headers)

        assert response.json()["success"] is True

    def test_returns_404_for_nonexistent_key(self, client, auth_headers):
        response = client.delete(
            f"/api-keys/{uuid4()}", headers=auth_headers
        )

        assert response.status_code == 404


class TestApiKeyAuth:
    def test_api_key_authenticates_text_reader_endpoint(self, client, auth_headers):
        # Create an API key via JWT
        create_response = client.post(
            "/api-keys",
            json={"name": "auth-test-key"},
            headers=auth_headers,
        )
        raw_key = create_response.json()["raw_key"]

        # Use the API key to access a text-reader endpoint
        response = client.post(
            "/text-reader/people",
            json={"name": "API Key Person"},
            headers={"X-API-Key": raw_key},
        )

        assert response.status_code == 200

    def test_invalid_api_key_returns_401(self, client):
        response = client.post(
            "/text-reader/people",
            json={"name": "API Key Person"},
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401

    def test_deactivated_key_returns_401(self, client, auth_headers):
        # Create and deactivate an API key
        create_response = client.post(
            "/api-keys",
            json={"name": "deactivated-key"},
            headers=auth_headers,
        )
        raw_key = create_response.json()["raw_key"]
        key_id = create_response.json()["id"]
        client.delete(f"/api-keys/{key_id}", headers=auth_headers)

        response = client.post(
            "/text-reader/people",
            json={"name": "Test Person"},
            headers={"X-API-Key": raw_key},
        )

        assert response.status_code == 401


# --- Text Reader Source Endpoints ---


class TestCreateTextReaderSource:
    def test_returns_200(self, client, auth_headers):
        response = client.post(
            "/text-reader/sources",
            json={
                "title": "A General History of Music",
                "author": "Charles Burney",
                "publisher": "Payne and Son",
                "pub_date": "1789",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_title(self, client, auth_headers):
        response = client.post(
            "/text-reader/sources",
            json={
                "title": "Music History",
                "author": "Author",
                "publisher": "Publisher",
            },
            headers=auth_headers,
        )

        assert response.json()["title"] == "Music History"

    def test_requires_auth(self, client):
        response = client.post(
            "/text-reader/sources",
            json={
                "title": "Title",
                "author": "Author",
                "publisher": "Publisher",
            },
        )

        assert response.status_code == 401


# --- Text Reader People Endpoints ---


class TestCreateTextReaderPerson:
    def test_returns_200(self, client, auth_headers):
        response = client.post(
            "/text-reader/people",
            json={"name": "Charles Burney"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_name(self, client, auth_headers):
        response = client.post(
            "/text-reader/people",
            json={"name": "George Handel"},
            headers=auth_headers,
        )

        assert response.json()["name"] == "George Handel"

    def test_returns_id(self, client, auth_headers):
        response = client.post(
            "/text-reader/people",
            json={"name": "Antonio Vivaldi"},
            headers=auth_headers,
        )

        assert response.json()["id"] is not None


class TestSearchTextReaderPeople:
    def test_returns_200(self, client, auth_headers):
        # Create a person first
        client.post(
            "/text-reader/people",
            json={"name": "Searchable Person"},
            headers=auth_headers,
        )

        response = client.get(
            "/text-reader/people/search",
            params={"name": "Searchable Person"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_candidates(self, client, auth_headers):
        client.post(
            "/text-reader/people",
            json={"name": "Johann Bach"},
            headers=auth_headers,
        )

        response = client.get(
            "/text-reader/people/search",
            params={"name": "Johann Bach"},
            headers=auth_headers,
        )

        assert len(response.json()["candidates"]) > 0

    def test_returns_empty_for_no_match(self, client, auth_headers):
        response = client.get(
            "/text-reader/people/search",
            params={"name": "xyznonexistent999"},
            headers=auth_headers,
        )

        assert response.json()["candidates"] == []


# --- Text Reader Places Endpoints ---


class TestCreateTextReaderPlace:
    def test_returns_200(self, client, auth_headers):
        response = client.post(
            "/text-reader/places",
            json={"name": "Leipzig", "latitude": 51.3, "longitude": 12.4},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_coordinates(self, client, auth_headers):
        response = client.post(
            "/text-reader/places",
            json={"name": "Vienna", "latitude": 48.2, "longitude": 16.4},
            headers=auth_headers,
        )

        data = response.json()
        assert data["latitude"] == 48.2
        assert data["longitude"] == 16.4


class TestSearchTextReaderPlaces:
    def test_returns_200(self, client, auth_headers):
        client.post(
            "/text-reader/places",
            json={"name": "Searchable Place", "latitude": 50.0, "longitude": 10.0},
            headers=auth_headers,
        )

        response = client.get(
            "/text-reader/places/search",
            params={"name": "Searchable Place"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_finds_by_coordinates(self, client, auth_headers):
        client.post(
            "/text-reader/places",
            json={"name": "Coordinate Place", "latitude": 55.0, "longitude": 15.0},
            headers=auth_headers,
        )

        response = client.get(
            "/text-reader/places/search",
            params={"latitude": 55.0, "longitude": 15.0, "radius": 0.5},
            headers=auth_headers,
        )

        assert len(response.json()["candidates"]) > 0


# --- Text Reader Time Endpoints ---


class TestCreateTextReaderTime:
    def test_returns_200(self, client, auth_headers):
        response = client.post(
            "/text-reader/times",
            json={
                "name": "1720",
                "date": "+1720-00-00T00:00:00Z",
                "calendar_model": "Q1985727",
                "precision": 9,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_date(self, client, auth_headers):
        response = client.post(
            "/text-reader/times",
            json={
                "name": "1721",
                "date": "+1721-00-00T00:00:00Z",
                "calendar_model": "Q1985727",
                "precision": 9,
            },
            headers=auth_headers,
        )

        assert response.json()["date"] == "+1721-00-00T00:00:00Z"


# --- Text Reader Story Endpoints ---


class TestCreateTextReaderStory:
    def test_returns_200(self, client, auth_headers):
        response = client.post(
            "/text-reader/stories",
            json={"name": "Test Story"},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_returns_name(self, client, auth_headers):
        response = client.post(
            "/text-reader/stories",
            json={"name": "My Story"},
            headers=auth_headers,
        )

        assert response.json()["name"] == "My Story"


class TestGetStoryBySource:
    def test_returns_null_when_not_found(self, client, auth_headers):
        response = client.get(
            f"/text-reader/stories/by-source/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json() is None

    def test_returns_story_for_source(self, client, auth_headers):
        # Create source
        source_response = client.post(
            "/text-reader/sources",
            json={
                "title": "Story Source Title",
                "author": "Author",
                "publisher": "Publisher",
            },
            headers=auth_headers,
        )
        source_id = source_response.json()["id"]

        # Create story with source
        client.post(
            "/text-reader/stories",
            json={"name": "Sourced Story", "source_id": source_id},
            headers=auth_headers,
        )

        response = client.get(
            f"/text-reader/stories/by-source/{source_id}",
            headers=auth_headers,
        )

        assert response.json()["name"] == "Sourced Story"


# --- Text Reader Event Endpoint ---


class TestCreateTextReaderEvent:
    def test_end_to_end_event_creation(self, client, auth_headers):
        # Create source
        source = client.post(
            "/text-reader/sources",
            json={
                "title": "E2E Source",
                "author": "Author",
                "publisher": "Publisher",
            },
            headers=auth_headers,
        ).json()

        # Create story
        story = client.post(
            "/text-reader/stories",
            json={"name": "E2E Story", "source_id": source["id"]},
            headers=auth_headers,
        ).json()

        # Create entities
        person = client.post(
            "/text-reader/people",
            json={"name": "E2E Person"},
            headers=auth_headers,
        ).json()

        place = client.post(
            "/text-reader/places",
            json={"name": "E2E Place", "latitude": 48.2, "longitude": 16.4},
            headers=auth_headers,
        ).json()

        time = client.post(
            "/text-reader/times",
            json={
                "name": "1750",
                "date": "+1750-00-00T00:00:00Z",
                "calendar_model": "Q1985727",
                "precision": 9,
            },
            headers=auth_headers,
        ).json()

        # Create event
        response = client.post(
            "/text-reader/events",
            json={
                "summary": "E2E Person visited E2E Place in 1750.",
                "tags": [
                    {
                        "id": person["id"],
                        "name": "E2E Person",
                        "start_char": 0,
                        "stop_char": 10,
                    },
                    {
                        "id": place["id"],
                        "name": "E2E Place",
                        "start_char": 19,
                        "stop_char": 28,
                    },
                    {
                        "id": time["id"],
                        "name": "1750",
                        "start_char": 32,
                        "stop_char": 36,
                    },
                ],
                "citation": {
                    "text": "Burney, vol. 1, p. 42",
                    "page_num": 42,
                    "access_date": "2026-03-11",
                },
                "source_id": source["id"],
                "story_id": story["id"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] is not None


# --- Summary Match Endpoint ---


class TestFindMatchingSummary:
    def test_returns_not_found(self, client, auth_headers):
        response = client.get(
            "/text-reader/summaries/match",
            params={
                "personIds": [str(uuid4())],
                "placeId": str(uuid4()),
                "datetime": "+1720-00-00T00:00:00Z",
                "calendarModel": "Q1985727",
                "precision": 9,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["found"] is False
