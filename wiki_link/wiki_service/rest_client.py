import requests
import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from wiki_service.config import WikiServiceConfig


class RestClientError(Exception):
    pass


class RestClient:
    def __init__(self, config: WikiServiceConfig):
        self._base_url = config.server_base_url
        self._session = requests.Session()
        # Get auth token
        response = self._session.post(
            f"{self._base_url}/token",
            data={"username": config.username, "password": config.password},
        )
        if not response.ok:
            raise RestClientError(f"Failed to authenticate: {response.text}")
        self._session.headers.update(
            {"Authorization": f"Bearer {response.json()['access_token']}"}
        )

    def get_tags(self, wikidata_ids: List[str]) -> dict:
        """Get existing tags by their WikiData IDs"""
        response = self._session.get(
            f"{self._base_url}/wikidata/tags", params={"wikidata_ids": wikidata_ids}
        )
        if not response.ok:
            raise RestClientError(f"Failed to get tags: {response.text}")
        return response.json()

    def create_person(
        self,
        name: str,
        wikidata_id: str,
        wikidata_url: str,
        description: str | None = None,
    ) -> dict:
        """Create a new person tag"""
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

    def create_event(
        self, summary: str, tags: List[dict], citation: dict, after: list[UUID]
    ) -> dict:
        """Create a new event"""
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
