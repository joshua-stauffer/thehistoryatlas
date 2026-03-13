"""Tests for entity resolver."""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4, UUID

from text_reader.entity_resolver import EntityResolver
from text_reader.types import (
    ExtractedEvent,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedTime,
)


@pytest.fixture
def mock_rest():
    return MagicMock()


@pytest.fixture
def mock_claude():
    return MagicMock()


@pytest.fixture
def mock_geonames():
    client = MagicMock()
    client.available = False
    return client


@pytest.fixture
def resolver(mock_rest, mock_claude, mock_geonames):
    return EntityResolver(
        rest_client=mock_rest,
        claude_client=mock_claude,
        geonames_client=mock_geonames,
    )


def make_event(
    summary="Bach visited Leipzig in 1723.",
    excerpt="Bach settled in Leipzig in the year 1723 as Thomaskantor.",
    person_name="Johann Sebastian Bach",
    place_name="Leipzig",
    time_name="1723",
):
    return ExtractedEvent(
        summary=summary,
        excerpt=excerpt,
        people=[ExtractedPerson(name=person_name)],
        place=ExtractedPlace(name=place_name, latitude=51.3, longitude=12.4),
        time=ExtractedTime(
            name=time_name,
            date="+1723-00-00T00:00:00Z",
            precision=9,
        ),
        confidence=0.9,
    )


def _stub_place_and_time(mock_rest):
    """Set up default mock returns for place and time resolution."""
    mock_rest.search_places.return_value = []
    mock_rest.create_place.return_value = {
        "id": str(uuid4()),
        "name": "Place",
        "latitude": 50.0,
        "longitude": 10.0,
    }
    mock_rest.check_time_exists.return_value = None
    mock_rest.create_time.return_value = {"id": str(uuid4()), "name": "1723"}


class TestResolvePersonCreatesNew:
    def test_creates_person_when_no_candidates(self, resolver, mock_rest, mock_claude):
        person_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {
            "id": str(person_id),
            "name": "New Person",
        }
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event = make_event(person_name="New Person")
        result = resolver.resolve_event(event)

        assert result.people[0].id == person_id

    def test_creates_person_when_claude_finds_no_match(
        self, resolver, mock_rest, mock_claude
    ):
        person_id = uuid4()
        mock_rest.search_people.return_value = [
            {"id": str(uuid4()), "name": "Different Person"}
        ]
        mock_claude.pick_best_entity_match.return_value = None
        mock_rest.create_person.return_value = {"id": str(person_id), "name": "Bach"}
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event = make_event(person_name="Bach")
        result = resolver.resolve_event(event)

        assert result.people[0].id == person_id


class TestResolvePersonMatchesExisting:
    def test_uses_matched_person(self, resolver, mock_rest, mock_claude):
        existing_id = uuid4()
        mock_rest.search_people.return_value = [
            {"id": str(existing_id), "name": "J.S. Bach"}
        ]
        mock_claude.pick_best_entity_match.return_value = existing_id
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event = make_event(person_name="J.S. Bach")
        result = resolver.resolve_event(event)

        assert result.people[0].id == existing_id

    def test_does_not_call_create(self, resolver, mock_rest, mock_claude):
        existing_id = uuid4()
        mock_rest.search_people.return_value = [
            {"id": str(existing_id), "name": "Handel"}
        ]
        mock_claude.pick_best_entity_match.return_value = existing_id
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event = make_event(person_name="Handel")
        resolver.resolve_event(event)

        mock_rest.create_person.assert_not_called()


class TestResolvePersonCache:
    def test_caches_resolved_person(self, resolver, mock_rest, mock_claude):
        person_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {
            "id": str(person_id),
            "name": "Cached Person",
        }
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event1 = make_event(person_name="Cached Person")
        event2 = make_event(
            summary="Cached Person visited Vienna in 1723.",
            person_name="Cached Person",
            place_name="Vienna",
        )

        resolver.resolve_event(event1)
        resolver.resolve_event(event2)

        assert mock_rest.create_person.call_count == 1


class TestResolveEventPassthrough:
    def test_preserves_excerpt(self, resolver, mock_rest, mock_claude):
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.find_matching_summary.return_value = {"found": False}
        _stub_place_and_time(mock_rest)

        event = make_event(excerpt="The exact passage from the source text.")
        result = resolver.resolve_event(event)

        assert result.excerpt == "The exact passage from the source text."


class TestResolvePlaceCreatesNew:
    def test_creates_place_when_no_candidates(self, resolver, mock_rest, mock_claude):
        place_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(place_id),
            "name": "New Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = None
        mock_rest.create_time.return_value = {"id": str(uuid4()), "name": "1723"}
        mock_rest.find_matching_summary.return_value = {"found": False}

        event = make_event(place_name="New Place")
        result = resolver.resolve_event(event)

        assert result.place.id == place_id


class TestResolvePlaceWithGeonames:
    def test_uses_geonames_coordinates(
        self, resolver, mock_rest, mock_claude, mock_geonames
    ):
        mock_geonames.available = True
        mock_geonames.search.return_value = {
            "name": "Leipzig",
            "latitude": 51.34,
            "longitude": 12.37,
            "geonames_id": 2879139,
        }
        place_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(place_id),
            "name": "Leipzig",
        }
        mock_rest.check_time_exists.return_value = None
        mock_rest.create_time.return_value = {"id": str(uuid4())}
        mock_rest.find_matching_summary.return_value = {"found": False}

        event = make_event()
        resolver.resolve_event(event)

        call_kwargs = mock_rest.create_place.call_args
        assert call_kwargs[1]["geonames_id"] == 2879139


class TestResolveTimeCreatesNew:
    def test_creates_time_when_not_exists(self, resolver, mock_rest, mock_claude):
        time_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(uuid4()),
            "name": "Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = None
        mock_rest.create_time.return_value = {"id": str(time_id), "name": "1723"}
        mock_rest.find_matching_summary.return_value = {"found": False}

        event = make_event()
        result = resolver.resolve_event(event)

        assert result.time.id == time_id


class TestResolveTimeUsesExisting:
    def test_uses_existing_time(self, resolver, mock_rest, mock_claude):
        existing_time_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(uuid4()),
            "name": "Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = existing_time_id
        mock_rest.find_matching_summary.return_value = {"found": False}

        event = make_event()
        result = resolver.resolve_event(event)

        assert result.time.id == existing_time_id

    def test_does_not_call_create(self, resolver, mock_rest, mock_claude):
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(uuid4()),
            "name": "Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = uuid4()
        mock_rest.find_matching_summary.return_value = {"found": False}

        event = make_event()
        resolver.resolve_event(event)

        mock_rest.create_time.assert_not_called()


class TestResolveDuplicateDetection:
    def test_marks_duplicate(self, resolver, mock_rest, mock_claude):
        summary_id = uuid4()
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(uuid4()),
            "name": "Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = None
        mock_rest.create_time.return_value = {"id": str(uuid4())}
        mock_rest.find_matching_summary.return_value = {
            "found": True,
            "summary_id": str(summary_id),
            "has_wikidata_citation": True,
        }

        event = make_event()
        result = resolver.resolve_event(event)

        assert result.is_duplicate is True

    def test_reports_wikidata_citation(self, resolver, mock_rest, mock_claude):
        mock_rest.search_people.return_value = []
        mock_rest.create_person.return_value = {"id": str(uuid4()), "name": "Person"}
        mock_rest.search_places.return_value = []
        mock_rest.create_place.return_value = {
            "id": str(uuid4()),
            "name": "Place",
            "latitude": 50.0,
            "longitude": 10.0,
        }
        mock_rest.check_time_exists.return_value = None
        mock_rest.create_time.return_value = {"id": str(uuid4())}
        mock_rest.find_matching_summary.return_value = {
            "found": True,
            "summary_id": str(uuid4()),
            "has_wikidata_citation": True,
        }

        event = make_event()
        result = resolver.resolve_event(event)

        assert result.duplicate_has_wikidata is True
