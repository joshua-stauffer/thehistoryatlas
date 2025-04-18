import requests
import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from wiki_service.config import WikiServiceConfig
from wiki_service.tracing import trace_time


class RestClientError(Exception):
    pass


class RestClient:
    def __init__(self, config: WikiServiceConfig):
        self._base_url = config.server_base_url
        self._config = config
        self._session = requests.Session()
        self._refresh_by = config.TOKEN_REFRESH_BY
        self._token_time = None
        # Get auth token
        self._authenticate()

    @trace_time()
    def _authenticate(self):
        """Authenticate with the server and get a token"""
        response = self._session.post(
            f"{self._base_url}/token",
            data={"username": self._config.username, "password": self._config.password},
        )
        if not response.ok:
            raise RestClientError(f"Failed to authenticate: {response.text}")
        self._session.headers.update(
            {"Authorization": f"Bearer {response.json()['access_token']}"}
        )
        # Update token timestamp
        self._token_time = datetime.now(timezone.utc)

    def _check_token_refresh(self):
        """Check if the authentication token needs refreshing"""
        if not self._token_time:
            return self._authenticate()

        now = datetime.now(timezone.utc)
        elapsed = (now - self._token_time).total_seconds()

        if elapsed >= self._refresh_by:
            self._authenticate()

    @trace_time()
    def get_tags(self, wikidata_ids: List[str]) -> dict:
        """Get existing tags by their WikiData IDs"""
        self._check_token_refresh()
        response = self._session.get(
            f"{self._base_url}/wikidata/tags", params={"wikidata_ids": wikidata_ids}
        )
        if not response.ok:
            raise RestClientError(f"Failed to get tags: {response.text}")
        return response.json()

    @trace_time()
    def create_person(
        self,
        name: str,
        wikidata_id: str,
        wikidata_url: str,
        description: str | None = None,
    ) -> dict:
        """Create a new person tag"""
        self._check_token_refresh()
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
            "description": description,
        }
        response = self._session.post(
            f"{self._base_url}/wikidata/people",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create person: {response.text}")
        return response.json()

    @trace_time()
    def create_place(
        self,
        name: str,
        wikidata_id: str,
        wikidata_url: str,
        latitude: float,
        longitude: float,
        description: str | None = None,
    ) -> dict:
        """Create a new place tag"""
        self._check_token_refresh()
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
            "latitude": latitude,
            "longitude": longitude,
            "description": description,
        }
        response = self._session.post(
            f"{self._base_url}/wikidata/places",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create place: {response.text}")
        return response.json()

    @trace_time()
    def create_time(
        self,
        name: str,
        wikidata_id: str | None,
        wikidata_url: str | None,
        date: str,
        calendar_model: str,
        precision: int,
        description: str | None = None,
    ) -> dict:
        """Create a new time tag"""
        self._check_token_refresh()
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
            "date": date,
            "calendar_model": calendar_model,
            "precision": precision,
            "description": description,
        }
        response = self._session.post(
            f"{self._base_url}/wikidata/times",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create time: {response.text}")
        return response.json()

    @trace_time()
    def check_time_exists(
        self,
        datetime: str,
        calendar_model: str,
        precision: int,
    ) -> Optional[UUID]:
        """Check if a time with the given attributes exists in the database.

        Args:
            datetime: The datetime string to check
            calendar_model: The calendar model to check
            precision: The time precision to check

        Returns:
            UUID if a matching time exists, None otherwise

        Raises:
            RestClientError: If the API request fails
        """
        self._check_token_refresh()
        data = {
            "datetime": datetime,
            "calendar_model": calendar_model,
            "precision": precision,
        }
        response = self._session.post(
            f"{self._base_url}/times/exist",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to check time existence: {response.text}")

        result = response.json()
        return UUID(result["id"]) if result["id"] else None

    @trace_time()
    def create_event(
        self, summary: str, tags: List[dict], citation: dict, after: list[UUID]
    ) -> dict:
        """Create a new event"""
        self._check_token_refresh()
        data = {
            "summary": summary,
            "tags": tags,
            "citation": citation,
            "after": [str(id) for id in after],
        }
        response = self._session.post(
            f"{self._base_url}/wikidata/events",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create event: {response.text}")
        return response.json()
