import json
import logging
from uuid import UUID

import anthropic

from text_reader.types import (
    ExtractedEvent,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedTime,
)

log = logging.getLogger(__name__)

MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20250401",
    "sonnet": "claude-sonnet-4-6-20250415",
    "opus": "claude-opus-4-6-20250415",
}

EXTRACTION_SYSTEM_PROMPT = """You are a scholarly research assistant specializing in historical text analysis. Your job is to extract structured historical events from source texts.

For each distinct historical event described in the text, extract:

1. **Summary**: A single sentence describing the event, written in third person past tense. The summary MUST contain the person's name, the place name, and a time reference as substrings (these will be tagged).

2. **People**: Each person mentioned in the event. Include:
   - name: Full name as it appears (or the most complete form used)
   - description: Brief identifying description (e.g., "English composer", "King of France")

3. **Place**: The location where the event occurred. Include:
   - name: Place name
   - latitude/longitude: Approximate coordinates if you can determine them (null if unknown)
   - description: Brief description

4. **Time**: When the event occurred. Include:
   - name: Human-readable date (e.g., "1759", "March 1685", "14 June 1770")
   - date: ISO-8601 formatted with leading +/- (e.g., "+1759-00-00T00:00:00Z", "+1685-03-00T00:00:00Z")
   - precision: 9 for year, 10 for month, 11 for day
   - calendar_model: "http://www.wikidata.org/entity/Q1985727" (Gregorian)

5. **Excerpt**: The verbatim sentence or short passage from the source text that supports this event. Copy it exactly as it appears in the source — do not paraphrase or summarize.

6. **Confidence**: A score from 0.0 to 1.0 indicating how confident you are in the extraction accuracy.

Rules:
- Only extract events with concrete people, places, AND times. Skip vague references.
- The summary text must literally contain the person name, place name, and time name as substrings.
- Use the most specific date precision available (day > month > year).
- For BCE dates, use negative years (e.g., "-0500-00-00T00:00:00Z").
- Each event should be a single, discrete historical occurrence.
- Prefer quality over quantity — skip uncertain or poorly-supported events.

Return a JSON array of events. Example:
```json
[
  {
    "summary": "George Frideric Handel performed at the court of Hanover in 1710.",
    "excerpt": "Handel was received at the court of Hanover with great distinction in the year 1710.",
    "people": [{"name": "George Frideric Handel", "description": "German-British Baroque composer"}],
    "place": {"name": "Hanover", "latitude": 52.3759, "longitude": 9.732, "description": "Capital of the Electorate of Hanover"},
    "time": {"name": "1710", "date": "+1710-00-00T00:00:00Z", "precision": 9},
    "confidence": 0.85
  }
]
```

Return ONLY the JSON array, no other text."""

ENTITY_MATCH_SYSTEM_PROMPT = """You are helping match extracted historical entities to existing database records.

Given an entity name and type, and a list of candidate matches from the database, determine if any candidate is the same entity. Consider name variations, historical spelling differences, and alternative forms.

Return a JSON object:
- If a match is found: {"match": true, "id": "<the matching candidate's id>"}
- If no match: {"match": false, "id": null}

Return ONLY the JSON object."""


class ClaudeClient:
    def __init__(self, api_key: str, model: str = "haiku"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = MODEL_MAP.get(model, model)
        log.info(f"Using Claude model: {self._model}")

    def extract_events(
        self, chunk_text: str, source_title: str, source_author: str
    ) -> list[ExtractedEvent]:
        """Extract historical events from a text chunk."""
        user_message = (
            f"Extract historical events from this passage of "
            f'"{source_title}" by {source_author}:\n\n{chunk_text}'
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=EXTRACTION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as e:
            log.error(f"Claude API error during extraction: {e}")
            return []

        content = response.content[0].text.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = (
                "\n".join(lines[1:-1])
                if lines[-1].strip() == "```"
                else "\n".join(lines[1:])
            )

        try:
            raw_events = json.loads(content)
        except json.JSONDecodeError:
            log.error(f"Failed to parse Claude response as JSON: {content[:200]}")
            return []

        events = []
        for raw in raw_events:
            try:
                event = ExtractedEvent(
                    summary=raw["summary"],
                    excerpt=raw["excerpt"],
                    people=[ExtractedPerson(**p) for p in raw.get("people", [])],
                    place=ExtractedPlace(**raw["place"]),
                    time=ExtractedTime(**raw["time"]),
                    confidence=raw.get("confidence", 0.5),
                )
                events.append(event)
            except (KeyError, TypeError, ValueError) as e:
                log.warning(f"Skipping malformed event: {e}")
                continue

        log.info(f"Extracted {len(events)} events from chunk")
        return events

    def pick_best_entity_match(
        self,
        entity_name: str,
        entity_type: str,
        candidates: list[dict],
    ) -> UUID | None:
        """Use Claude to pick the best matching entity from candidates."""
        if not candidates:
            return None

        candidates_text = "\n".join(
            f"- id: {c['id']}, name: {c['name']}" for c in candidates
        )

        user_message = (
            f"Entity to match:\n"
            f"- Name: {entity_name}\n"
            f"- Type: {entity_type}\n\n"
            f"Candidates:\n{candidates_text}"
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=256,
                system=ENTITY_MATCH_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as e:
            log.error(f"Claude API error during entity matching: {e}")
            return None

        content = response.content[0].text.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = (
                "\n".join(lines[1:-1])
                if lines[-1].strip() == "```"
                else "\n".join(lines[1:])
            )

        try:
            result = json.loads(content)
            if result.get("match") and result.get("id"):
                return UUID(result["id"])
        except (json.JSONDecodeError, ValueError) as e:
            log.warning(f"Failed to parse entity match response: {e}")

        return None
