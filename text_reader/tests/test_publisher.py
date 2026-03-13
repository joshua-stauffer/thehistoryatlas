"""Tests for publisher."""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from text_reader.publisher import Publisher
from text_reader.types import ResolvedEvent, ResolvedPerson, ResolvedPlace, ResolvedTime


@pytest.fixture
def mock_rest():
    return MagicMock()


@pytest.fixture
def publisher(mock_rest):
    return Publisher(rest_client=mock_rest)


def make_resolved_event(
    summary="Bach visited Leipzig in 1723.",
    excerpt="Bach was appointed Thomaskantor at Leipzig in 1723.",
    person_name="Bach",
    place_name="Leipzig",
    time_name="1723",
):
    return ResolvedEvent(
        summary=summary,
        excerpt=excerpt,
        people=[ResolvedPerson(id=uuid4(), name=person_name)],
        place=ResolvedPlace(id=uuid4(), name=place_name, latitude=51.3, longitude=12.4),
        time=ResolvedTime(
            id=uuid4(),
            name=time_name,
            date="+1723-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        ),
        page_num=42,
        confidence=0.9,
    )


class TestEnsureStory:
    def test_returns_existing_story_id(self, publisher, mock_rest):
        story_id = uuid4()
        mock_rest.get_story_by_source.return_value = {
            "id": str(story_id),
            "name": "Existing Story",
        }

        result = publisher.ensure_story(source_id=uuid4(), source_title="Test Source")

        assert result == story_id

    def test_creates_story_when_none_exists(self, publisher, mock_rest):
        story_id = uuid4()
        mock_rest.get_story_by_source.return_value = None
        mock_rest.create_story.return_value = {
            "id": str(story_id),
            "name": "From: Test Source",
        }

        result = publisher.ensure_story(source_id=uuid4(), source_title="Test Source")

        assert result == story_id

    def test_does_not_create_when_existing(self, publisher, mock_rest):
        mock_rest.get_story_by_source.return_value = {
            "id": str(uuid4()),
            "name": "Existing",
        }

        publisher.ensure_story(source_id=uuid4(), source_title="Test")

        mock_rest.create_story.assert_not_called()


class TestPublishEvent:
    def test_returns_summary_id(self, publisher, mock_rest):
        summary_id = uuid4()
        mock_rest.create_event.return_value = {"id": str(summary_id)}

        event = make_resolved_event()
        result = publisher.publish_event(
            event=event, source_id=uuid4(), story_id=uuid4()
        )

        assert result == summary_id

    def test_calls_create_event(self, publisher, mock_rest):
        mock_rest.create_event.return_value = {"id": str(uuid4())}

        event = make_resolved_event()
        publisher.publish_event(event=event, source_id=uuid4(), story_id=uuid4())

        mock_rest.create_event.assert_called_once()

    def test_citation_text_uses_excerpt(self, publisher, mock_rest):
        mock_rest.create_event.return_value = {"id": str(uuid4())}

        event = make_resolved_event(
            excerpt="The verbatim passage from the original text.",
        )
        publisher.publish_event(event=event, source_id=uuid4(), story_id=uuid4())

        call_kwargs = mock_rest.create_event.call_args[1]
        assert (
            call_kwargs["citation"]["text"]
            == "The verbatim passage from the original text."
        )

    def test_returns_none_on_error(self, publisher, mock_rest):
        mock_rest.create_event.side_effect = Exception("server error")

        event = make_resolved_event()
        result = publisher.publish_event(
            event=event, source_id=uuid4(), story_id=uuid4()
        )

        assert result is None


class TestBuildTags:
    def test_finds_person_in_summary(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig in 1723.",
            person_name="Bach",
        )

        tags = publisher._build_tags(event)

        person_tags = [t for t in tags if t["name"] == "Bach"]
        assert len(person_tags) == 1

    def test_finds_place_in_summary(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig in 1723.",
            place_name="Leipzig",
        )

        tags = publisher._build_tags(event)

        place_tags = [t for t in tags if t["name"] == "Leipzig"]
        assert len(place_tags) == 1

    def test_finds_time_in_summary(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig in 1723.",
            time_name="1723",
        )

        tags = publisher._build_tags(event)

        time_tags = [t for t in tags if t["name"] == "1723"]
        assert len(time_tags) == 1

    def test_returns_correct_start_char(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig in 1723.",
            person_name="Bach",
        )

        tags = publisher._build_tags(event)

        person_tag = next(t for t in tags if t["name"] == "Bach")
        assert person_tag["start_char"] == 0

    def test_returns_correct_stop_char(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig in 1723.",
            person_name="Bach",
        )

        tags = publisher._build_tags(event)

        person_tag = next(t for t in tags if t["name"] == "Bach")
        assert person_tag["stop_char"] == 4

    def test_returns_empty_when_place_not_found(self, publisher):
        event = make_resolved_event(
            summary="Someone was somewhere sometime.",
            place_name="NotInText",
            time_name="sometime",
        )

        tags = publisher._build_tags(event)

        assert tags == []

    def test_returns_empty_when_time_not_found(self, publisher):
        event = make_resolved_event(
            summary="Bach visited Leipzig sometime.",
            place_name="Leipzig",
            time_name="NotInText",
        )

        tags = publisher._build_tags(event)

        assert tags == []
