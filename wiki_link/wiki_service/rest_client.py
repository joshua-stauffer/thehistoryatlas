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
        self._base_url = f"http://{config.server_base_url}"
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

    def create_person(self, name: str, wikidata_id: str, wikidata_url: str) -> dict:
        """Create a new person tag"""
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
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
    ) -> dict:
        """Create a new place tag"""
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
            "latitude": latitude,
            "longitude": longitude,
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
    ) -> dict:
        """Create a new time tag"""
        data = {
            "name": name,
            "wikidata_id": wikidata_id,
            "wikidata_url": wikidata_url,
            "date": date,
            "calendar_model": calendar_model,
            "precision": precision,
        }
        response = self._session.post(
            f"{self._base_url}/wikidata/times",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create time: {response.text}")
        return response.json()

    def create_event(self, summary: str, tags: List[dict], citation: dict) -> dict:
        """Create a new event"""
        data = {"summary": summary, "tags": tags, "citation": citation}
        response = self._session.post(
            f"{self._base_url}/wikidata/events",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(f"Failed to create event: {response.text}")
        return response.json()
