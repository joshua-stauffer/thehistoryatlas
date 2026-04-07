"""Tests for Claude client."""

import json
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from text_reader.claude_client import ClaudeClient, MODEL_MAP


def _make_stream_ctx(response):
    """Wrap a mock response in a context-manager mock for messages.stream()."""
    ctx = MagicMock()
    ctx.__enter__.return_value.get_final_message.return_value = response
    return ctx


class TestModelMap:
    def test_haiku_maps_to_model_id(self):
        assert "haiku" in MODEL_MAP["haiku"]

    def test_sonnet_maps_to_model_id(self):
        assert "sonnet" in MODEL_MAP["sonnet"]

    def test_opus_maps_to_model_id(self):
        assert "opus" in MODEL_MAP["opus"]


def _make_valid_event_json(
    summary="Johann Sebastian Bach visited Leipzig in 1723.",
    excerpt="Bach made his way to Leipzig in the year 1723.",
    person_name="Johann Sebastian Bach",
    place_name="Leipzig",
    time_name="1723",
    time_date="+1723-00-00T00:00:00Z",
):
    return {
        "summary": summary,
        "excerpt": excerpt,
        "people": [{"name": person_name, "description": "German composer"}],
        "place": {"name": place_name, "latitude": 51.3, "longitude": 12.4},
        "time": {"name": time_name, "date": time_date, "precision": 9},
        "confidence": 0.9,
    }


class TestExtractEvents:
    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_list_of_events(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text=json.dumps([_make_valid_event_json()]))]
        mock_client.messages.stream.return_value = _make_stream_ctx(mock_response)

        client = ClaudeClient(api_key="fake-key", model="haiku")
        result = client.extract_events("chunk text", "Source", "Author")

        assert len(result) == 1

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_extracts_summary(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        summary = "George Frideric Handel performed in London in 1711."
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    [
                        _make_valid_event_json(
                            summary=summary,
                            person_name="George Frideric Handel",
                            place_name="London",
                            time_name="1711",
                            time_date="+1711-00-00T00:00:00Z",
                        )
                    ]
                )
            )
        ]
        mock_client.messages.stream.return_value = _make_stream_ctx(mock_response)

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result[0].summary == summary

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_strips_markdown_fences(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        fenced = "```json\n" + json.dumps([_make_valid_event_json()]) + "\n```"
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text=fenced)]
        mock_client.messages.stream.return_value = _make_stream_ctx(mock_response)

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 1

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_empty_on_invalid_json(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="not valid json")]
        mock_client.messages.stream.return_value = _make_stream_ctx(mock_response)

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_empty_on_api_error(self, mock_anthropic_cls):
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.stream.side_effect = anthropic.APIError(
            message="rate limit",
            request=MagicMock(),
            body=None,
        )

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_skips_malformed_events(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        events_json = json.dumps(
            [_make_valid_event_json(), {"summary": "Missing place and time"}]
        )
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text=events_json)]
        mock_client.messages.stream.return_value = _make_stream_ctx(mock_response)

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 1

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_invalid_summary_triggers_fix_call(self, mock_anthropic_cls):
        """An event whose summary omits a person name is sent back for fixing."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        bad_event = _make_valid_event_json(
            summary="Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )
        fixed_event = _make_valid_event_json(
            summary="George Frideric Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )

        extract_response = MagicMock()
        extract_response.stop_reason = "end_turn"
        extract_response.content = [MagicMock(text=json.dumps([bad_event]))]

        fix_response = MagicMock()
        fix_response.stop_reason = "end_turn"
        fix_response.content = [MagicMock(text=json.dumps([[fixed_event]]))]

        mock_client.messages.stream.side_effect = [
            _make_stream_ctx(extract_response),
            _make_stream_ctx(fix_response),
        ]

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 1
        assert result[0].summary == "George Frideric Handel performed in London in 1711."
        assert mock_client.messages.stream.call_count == 2

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_date_range_event_split_into_two(self, mock_anthropic_cls):
        """A date-range time name triggers a fix that splits the event in two."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        range_event = _make_valid_event_json(
            summary="Thomas Dipper was organist at King's Chapel, Boston from 1756 to 1762.",
            person_name="Thomas Dipper",
            place_name="Boston",
            time_name="1756-1762",
            time_date="+1756-00-00T00:00:00Z",
        )
        split_a = _make_valid_event_json(
            summary="Thomas Dipper became organist at King's Chapel in Boston in 1756.",
            person_name="Thomas Dipper",
            place_name="Boston",
            time_name="1756",
            time_date="+1756-00-00T00:00:00Z",
        )
        split_b = _make_valid_event_json(
            summary="Thomas Dipper left his position as organist at King's Chapel in Boston in 1762.",
            person_name="Thomas Dipper",
            place_name="Boston",
            time_name="1762",
            time_date="+1762-00-00T00:00:00Z",
        )

        extract_response = MagicMock()
        extract_response.stop_reason = "end_turn"
        extract_response.content = [MagicMock(text=json.dumps([range_event]))]

        fix_response = MagicMock()
        fix_response.stop_reason = "end_turn"
        fix_response.content = [MagicMock(text=json.dumps([[split_a, split_b]]))]

        mock_client.messages.stream.side_effect = [
            _make_stream_ctx(extract_response),
            _make_stream_ctx(fix_response),
        ]

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 2
        assert result[0].time.name == "1756"
        assert result[1].time.name == "1762"

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_event_dropped_if_still_invalid_after_fix(self, mock_anthropic_cls):
        """If the fixed summary still fails validation, the event is dropped."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        bad_event = _make_valid_event_json(
            summary="Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )
        still_bad = _make_valid_event_json(
            summary="Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )

        extract_response = MagicMock()
        extract_response.stop_reason = "end_turn"
        extract_response.content = [MagicMock(text=json.dumps([bad_event]))]

        fix_response = MagicMock()
        fix_response.stop_reason = "end_turn"
        fix_response.content = [MagicMock(text=json.dumps([[still_bad]]))]

        mock_client.messages.stream.side_effect = [
            _make_stream_ctx(extract_response),
            _make_stream_ctx(fix_response),
        ]

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_valid_events_not_affected_by_fix_pass(self, mock_anthropic_cls):
        """Valid events pass through even when other events need fixing."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        valid = _make_valid_event_json()
        bad = _make_valid_event_json(
            summary="Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )
        fixed = _make_valid_event_json(
            summary="George Frideric Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )

        extract_response = MagicMock()
        extract_response.stop_reason = "end_turn"
        extract_response.content = [MagicMock(text=json.dumps([valid, bad]))]

        fix_response = MagicMock()
        fix_response.stop_reason = "end_turn"
        fix_response.content = [MagicMock(text=json.dumps([[fixed]]))]

        mock_client.messages.stream.side_effect = [
            _make_stream_ctx(extract_response),
            _make_stream_ctx(fix_response),
        ]

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 2

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_max_tokens_splits_chunk_and_combines_results(self, mock_anthropic_cls):
        """When the response is truncated, the chunk is halved and each half reprocessed."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        event_a = _make_valid_event_json()
        event_b = _make_valid_event_json(
            summary="George Frideric Handel performed in London in 1711.",
            person_name="George Frideric Handel",
            place_name="London",
            time_name="1711",
            time_date="+1711-00-00T00:00:00Z",
        )

        truncated = MagicMock()
        truncated.stop_reason = "max_tokens"
        truncated.content = [MagicMock(text="[truncated json")]

        half_a = MagicMock()
        half_a.stop_reason = "end_turn"
        half_a.content = [MagicMock(text=json.dumps([event_a]))]

        half_b = MagicMock()
        half_b.stop_reason = "end_turn"
        half_b.content = [MagicMock(text=json.dumps([event_b]))]

        mock_client.messages.stream.side_effect = [
            _make_stream_ctx(truncated),
            _make_stream_ctx(half_a),
            _make_stream_ctx(half_b),
        ]

        # Use a chunk with a paragraph break so the split finds a natural boundary
        chunk = "first half text\n\nsecond half text"
        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events(
            chunk, "Source", "Author", start_page=10, end_page=15
        )

        assert len(result) == 2
        assert mock_client.messages.stream.call_count == 3

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_max_tokens_at_depth_2_parses_partial(self, mock_anthropic_cls):
        """At depth 2 the chunk is not split further; partial JSON is attempted."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        truncated = MagicMock()
        truncated.stop_reason = "max_tokens"
        truncated.content = [MagicMock(text="not valid json")]

        mock_client.messages.stream.return_value = _make_stream_ctx(truncated)

        client = ClaudeClient(api_key="fake-key")
        # Call with _depth=2 directly to simulate already-split state
        result = client.extract_events(
            "text", "Source", "Author", start_page=5, end_page=7, _depth=2
        )

        assert result == []
        assert mock_client.messages.stream.call_count == 1


class TestPickBestEntityMatch:
    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_none_for_empty_candidates(self, mock_anthropic_cls):
        mock_anthropic_cls.return_value = MagicMock()

        client = ClaudeClient(api_key="fake-key")
        result = client.pick_best_entity_match("Bach", "PERSON", [])

        assert result is None

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_matched_id(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        match_id = str(uuid4())
        response_json = json.dumps({"match": True, "id": match_id})
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.pick_best_entity_match(
            "Bach", "PERSON", [{"id": match_id, "name": "J.S. Bach"}]
        )

        assert str(result) == match_id

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_none_when_no_match(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        response_json = json.dumps({"match": False, "id": None})
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.pick_best_entity_match(
            "Unknown", "PERSON", [{"id": str(uuid4()), "name": "Someone Else"}]
        )

        assert result is None


class TestValidateEvent:
    """Tests for the _validate_event helper."""

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_valid_event_returns_empty_list(self, mock_anthropic_cls):
        mock_anthropic_cls.return_value = MagicMock()
        client = ClaudeClient(api_key="fake-key")
        event_data = _make_valid_event_json()
        from text_reader.types import ExtractedEvent, ExtractedPerson, ExtractedPlace, ExtractedTime
        event = ExtractedEvent(
            summary=event_data["summary"],
            excerpt=event_data["excerpt"],
            people=[ExtractedPerson(**p) for p in event_data["people"]],
            place=ExtractedPlace(**event_data["place"]),
            time=ExtractedTime(**event_data["time"]),
        )
        assert client._validate_event(event) == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_publication_event_with_editor_as_person(self, mock_anthropic_cls):
        """For a publication event the editor/author name must appear in the summary."""
        mock_anthropic_cls.return_value = MagicMock()
        client = ClaudeClient(api_key="fake-key")
        from text_reader.types import ExtractedEvent, ExtractedPerson, ExtractedPlace, ExtractedTime
        event = ExtractedEvent(
            summary="Waldo Selden Pratt edited Grove's Dictionary American Supplement in New York in November 1920.",
            excerpt="PRINTED IN THE UNITED STATES OF AMERICA. Published November, 1920.",
            people=[ExtractedPerson(name="Waldo Selden Pratt", description="American musicologist and editor")],
            place=ExtractedPlace(name="New York", latitude=40.71, longitude=-74.01),
            time=ExtractedTime(name="November 1920", date="+1920-11-00T00:00:00Z", precision=10),
        )
        assert client._validate_event(event) == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_missing_person_name_flagged(self, mock_anthropic_cls):
        """Summary that omits the person name is invalid."""
        mock_anthropic_cls.return_value = MagicMock()
        client = ClaudeClient(api_key="fake-key")
        from text_reader.types import ExtractedEvent, ExtractedPerson, ExtractedPlace, ExtractedTime
        event = ExtractedEvent(
            summary="Grove's Dictionary was published in New York in November 1920.",
            excerpt="Published November, 1920.",
            people=[ExtractedPerson(name="Waldo Selden Pratt", description="Editor")],
            place=ExtractedPlace(name="New York", latitude=40.71, longitude=-74.01),
            time=ExtractedTime(name="November 1920", date="+1920-11-00T00:00:00Z", precision=10),
        )
        missing = client._validate_event(event)
        assert "Waldo Selden Pratt" in missing
