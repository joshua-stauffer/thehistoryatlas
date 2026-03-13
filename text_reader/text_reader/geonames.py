import logging

import requests

log = logging.getLogger(__name__)


class GeoNamesClient:
    BASE_URL = "http://api.geonames.org/searchJSON"

    def __init__(self, username: str | None = None):
        self._username = username

    @property
    def available(self) -> bool:
        return self._username is not None

    def search(self, name: str) -> dict | None:
        """Search GeoNames for a place by name. Returns best match or None."""
        if not self._username:
            return None

        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    "q": name,
                    "maxRows": 1,
                    "username": self._username,
                    "style": "MEDIUM",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            log.warning(f"GeoNames lookup failed for '{name}': {e}")
            return None

        results = data.get("geonames", [])
        if not results:
            return None

        result = results[0]
        return {
            "name": result.get("name", name),
            "latitude": float(result["lat"]),
            "longitude": float(result["lng"]),
            "geonames_id": int(result["geonameId"]),
        }
