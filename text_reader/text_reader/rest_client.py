import json
import logging
from typing import Optional
from uuid import UUID

import requests

log = logging.getLogger(__name__)


class RestClientError(Exception):
    pass


class RestClient:
    def __init__(self, base_url: str, api_key: str):
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": api_key})

    def _post_json(self, path: str, data: dict) -> dict:
        response = self._session.post(
            f"{self._base_url}{path}",
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        if not response.ok:
            raise RestClientError(
                f"POST {path} failed ({response.status_code}): {response.text}"
            )
        return response.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        response = self._session.get(f"{self._base_url}{path}", params=params)
        if not response.ok:
            raise RestClientError(
                f"GET {path} failed ({response.status_code}): {response.text}"
            )
        return response.json()

    # --- Sources ---

    def create_source(
        self, title: str, author: str, publisher: str, pub_date: str | None
    ) -> dict:
        return self._post_json(
            "/text-reader/sources",
            {
                "title": title,
                "author": author,
                "publisher": publisher,
                "pub_date": pub_date,
            },
        )

    # --- People ---

    def search_people(self, name: str) -> list[dict]:
        result = self._get("/text-reader/people/search", params={"name": name})
        return result.get("candidates", [])

    def create_person(self, name: str, description: str | None = None) -> dict:
        return self._post_json(
            "/text-reader/people",
            {"name": name, "description": description},
        )

    # --- Places ---

    def search_places(
        self,
        name: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float = 1.0,
    ) -> list[dict]:
        params: dict = {}
        if name:
            params["name"] = name
        if latitude is not None:
            params["latitude"] = latitude
        if longitude is not None:
            params["longitude"] = longitude
        params["radius"] = radius
        result = self._get("/text-reader/places/search", params=params)
        return result.get("candidates", [])

    def create_place(
        self,
        name: str,
        latitude: float,
        longitude: float,
        geonames_id: int | None = None,
        description: str | None = None,
    ) -> dict:
        return self._post_json(
            "/text-reader/places",
            {
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
                "geonames_id": geonames_id,
                "description": description,
            },
        )

    # --- Times ---

    def check_time_exists(
        self, datetime: str, calendar_model: str, precision: int
    ) -> Optional[UUID]:
        result = self._post_json(
            "/times/exist",
            {
                "datetime": datetime,
                "calendar_model": calendar_model,
                "precision": precision,
            },
        )
        if result.get("id"):
            return UUID(result["id"])
        return None

    def create_time(
        self,
        name: str,
        date: str,
        calendar_model: str,
        precision: int,
        description: str | None = None,
    ) -> dict:
        return self._post_json(
            "/text-reader/times",
            {
                "name": name,
                "date": date,
                "calendar_model": calendar_model,
                "precision": precision,
                "description": description,
            },
        )

    # --- Events ---

    def create_event(
        self,
        summary: str,
        tags: list[dict],
        citation: dict,
        source_id: str,
        story_id: str,
    ) -> dict:
        return self._post_json(
            "/text-reader/events",
            {
                "summary": summary,
                "tags": tags,
                "citation": citation,
                "source_id": source_id,
                "story_id": story_id,
            },
        )

    # --- Summary Match ---

    def find_matching_summary(
        self,
        person_ids: list[UUID],
        place_id: UUID,
        datetime: str,
        calendar_model: str,
        precision: int,
    ) -> dict:
        params = {
            "personIds": [str(pid) for pid in person_ids],
            "placeId": str(place_id),
            "datetime": datetime,
            "calendarModel": calendar_model,
            "precision": precision,
        }
        return self._get("/text-reader/summaries/match", params=params)

    # --- Stories ---

    def create_story(
        self,
        name: str,
        description: str | None = None,
        source_id: str | None = None,
    ) -> dict:
        return self._post_json(
            "/text-reader/stories",
            {
                "name": name,
                "description": description,
                "source_id": source_id,
            },
        )

    def get_story_by_source(self, source_id: str) -> dict | None:
        try:
            return self._get(f"/text-reader/stories/by-source/{source_id}")
        except RestClientError:
            return None
