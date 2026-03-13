"""Tests for GeoNames client."""

import pytest
from unittest.mock import patch, MagicMock

from text_reader.geonames import GeoNamesClient


class TestGeoNamesAvailable:
    def test_available_with_username(self):
        client = GeoNamesClient(username="testuser")

        assert client.available is True

    def test_not_available_without_username(self):
        client = GeoNamesClient(username=None)

        assert client.available is False


class TestGeoNamesSearch:
    def test_returns_none_without_username(self):
        client = GeoNamesClient(username=None)

        result = client.search("London")

        assert result is None

    @patch("text_reader.geonames.requests.get")
    def test_returns_result_on_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "geonames": [
                {
                    "name": "London",
                    "lat": "51.5074",
                    "lng": "-0.1278",
                    "geonameId": 2643743,
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GeoNamesClient(username="testuser")
        result = client.search("London")

        assert result["name"] == "London"

    @patch("text_reader.geonames.requests.get")
    def test_returns_latitude(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "geonames": [
                {"name": "Paris", "lat": "48.8566", "lng": "2.3522", "geonameId": 123}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GeoNamesClient(username="testuser")
        result = client.search("Paris")

        assert abs(result["latitude"] - 48.8566) < 0.001

    @patch("text_reader.geonames.requests.get")
    def test_returns_none_for_empty_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"geonames": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GeoNamesClient(username="testuser")
        result = client.search("NonexistentPlace123")

        assert result is None

    @patch("text_reader.geonames.requests.get")
    def test_returns_none_on_request_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("timeout")

        client = GeoNamesClient(username="testuser")
        result = client.search("London")

        assert result is None
