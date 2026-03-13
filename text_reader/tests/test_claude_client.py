"""Tests for Claude client."""

import json
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from text_reader.claude_client import ClaudeClient, MODEL_MAP


class TestModelMap:
    def test_haiku_maps_to_model_id(self):
        assert "haiku" in MODEL_MAP["haiku"]

    def test_sonnet_maps_to_model_id(self):
        assert "sonnet" in MODEL_MAP["sonnet"]

    def test_opus_maps_to_model_id(self):
        assert "opus" in MODEL_MAP["opus"]


class TestExtractEvents:
    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_list_of_events(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        events_json = json.dumps(
            [
                {
                    "summary": "Bach visited Leipzig in 1723.",
                    "excerpt": "Bach made his way to Leipzig in the year 1723.",
                    "people": [
                        {
                            "name": "Johann Sebastian Bach",
                            "description": "German composer",
                        }
                    ],
                    "place": {"name": "Leipzig", "latitude": 51.3, "longitude": 12.4},
                    "time": {
                        "name": "1723",
                        "date": "+1723-00-00T00:00:00Z",
                        "precision": 9,
                    },
                    "confidence": 0.9,
                }
            ]
        )
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=events_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key", model="haiku")
        result = client.extract_events("chunk text", "Source", "Author")

        assert len(result) == 1

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_extracts_summary(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        events_json = json.dumps(
            [
                {
                    "summary": "Handel performed in London in 1711.",
                    "excerpt": "Handel gave a celebrated performance in London in 1711.",
                    "people": [{"name": "George Frideric Handel"}],
                    "place": {"name": "London"},
                    "time": {
                        "name": "1711",
                        "date": "+1711-00-00T00:00:00Z",
                        "precision": 9,
                    },
                }
            ]
        )
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=events_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result[0].summary == "Handel performed in London in 1711."

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_strips_markdown_fences(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        events_json = (
            "```json\n"
            + json.dumps(
                [
                    {
                        "summary": "Test event.",
                        "excerpt": "The original source text for the test event.",
                        "people": [{"name": "Person"}],
                        "place": {"name": "Place"},
                        "time": {
                            "name": "1700",
                            "date": "+1700-00-00T00:00:00Z",
                            "precision": 9,
                        },
                    }
                ]
            )
            + "\n```"
        )
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=events_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 1

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_empty_on_invalid_json(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert result == []

    @patch("text_reader.claude_client.anthropic.Anthropic")
    def test_returns_empty_on_api_error(self, mock_anthropic_cls):
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIError(
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

        # First event is valid, second is missing required fields
        events_json = json.dumps(
            [
                {
                    "summary": "Valid event.",
                    "excerpt": "The verbatim passage supporting the valid event.",
                    "people": [{"name": "Person"}],
                    "place": {"name": "Place"},
                    "time": {
                        "name": "1700",
                        "date": "+1700-00-00T00:00:00Z",
                        "precision": 9,
                    },
                },
                {"summary": "Missing place and time"},
            ]
        )
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=events_json)]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(api_key="fake-key")
        result = client.extract_events("text", "Source", "Author")

        assert len(result) == 1


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
