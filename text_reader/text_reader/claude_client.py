import json
import logging
import time
from uuid import UUID

import anthropic
import httpx

from text_reader.types import (
    ExtractedEvent,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedTime,
)

log = logging.getLogger(__name__)

MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
}

EXTRACTION_SYSTEM_PROMPT = """You are a scholarly research assistant specializing in historical text analysis. Your job is to extract structured historical events from source texts.

A single passage may yield multiple events — extract each discrete occurrence separately. Biographical entries commonly contain several distinct events: a birth, a death, career appointments, performances, relocations, publications, and so on. Extract all of them.

For each distinct historical event described in the text, extract:

1. **Summary**: A single sentence describing the event, written in third person past tense, using natural language. The summary MUST contain the person's full name, the place `name` (as defined below), and the time `name` as literal substrings — these will be used to locate tags in the text. Include meaningful detail — do not strip out occupations, roles, or qualifications that appear in the source. For example, prefer "John W. Bischoff worked as organist, singing-teacher, and song-writer in Washington from 1875" over a bare "John W. Bischoff was in Washington in 1875."

2. **People**: Each person mentioned in the event. Include:
   - name: Full name as it appears (or the most complete form used)
   - description: Brief identifying description (e.g., "English composer", "King of France")

3. **Place**: The location where the event occurred. Include:
   - name: The place name exactly as you write it in the summary — use natural, concise language (e.g. "New York", "Boston", "Paris"). This must match the summary verbatim.
   - qualified_name: The fully qualified name for disambiguation, including state or country. Spell out abbreviations (Pa. → Pennsylvania, N.Y. → New York, Mass. → Massachusetts, etc.). Examples: "New York, New York"; "Boston, Massachusetts"; "Ephrata, Pennsylvania"; "Leipzig, Germany". If the source gives a qualifier (e.g. "Ephrata, Pa."), always populate this field.
   - latitude/longitude: Approximate coordinates if you can determine them (null if unknown)
   - description: Brief description

4. **Time**: When the event occurred. Include:
   - name: Human-readable date (e.g., "1759", "March 1685", "14 June 1770")
   - date: ISO-8601 formatted with leading +/- (e.g., "+1759-00-00T00:00:00Z", "+1685-03-00T00:00:00Z")
   - precision: 9 for year, 10 for month, 11 for day
   - calendar_model: "http://www.wikidata.org/entity/Q1985727" (Gregorian)

5. **Excerpt**: The verbatim sentence or short passage from the source text that supports this event. Copy it exactly as it appears in the source — do not paraphrase or summarize.

6. **Confidence**: A score from 0.0 to 1.0 indicating how confident you are in the extraction accuracy.

Valid event types include (but are not limited to):
- Births, deaths, and relocations
- Career appointments, performances, teaching positions
- Publications: books, dictionaries, journals, sheet music — these are historical events. For a publication, the author or editor is the person; for example, "Waldo Selden Pratt edited Grove's Dictionary American Supplement in New York in November 1920" not "The Macmillan Company published…". Do not use a publishing house or organization as the person.
- Compositions, premieres, and recordings
- Instrument-making and manufacturing (e.g., a craftsman building the first piano of a type in a city)
- Institutional founding (conservatories, orchestras, music schools) — use the founder as the person

Rules:
- Only extract events with concrete individual people, places, AND times. Skip truly vague references with no specific date or location. Organizations and publishers are not acceptable substitutes for a named person.
- The summary must contain the person's name, the `place.name` value, and the `time.name` value as exact literal substrings. The `place.name` should be whatever natural form you used in the sentence (e.g. "New York", "Boston") — not the qualified form. The `place.qualified_name` is for disambiguation only and does not need to appear in the summary.
- Use the most specific date precision available (day > month > year).
- For BCE dates, use negative years (e.g., "-0500-00-00T00:00:00Z").
- Each event must have a single, discrete point in time — never a range. A date range like "1756-1762" or "1885-92" indicates two events: one at the start and one at the end. Extract them separately (e.g., "appointed organist in 1756" and "left the position in 1762"). The time name must be a single year, month, or day — never "1756-1762".
- Birth and death dates with locations (e.g., "b. Chicago, 1850" or "d. Paris, 1903") are valid events — extract them.
- Extract every qualifying event present in the passage, even if the passage is primarily a preface, table of contents, or bibliography. Do not skip a chunk just because most of it is vague — extract whatever specific events are present.

Return a JSON array of events. Example showing multiple events from one biographical entry:
```json
[
  {
    "summary": "John W. Bischoff was born in Chicago in 1850.",
    "excerpt": "Bischoff, John W. (Chicago, 1850-1909, Washington), trained at the Wisconsin Institute for the Blind and in London, from 1875 was organist, singing-teacher and song-writer at Washington.",
    "people": [{"name": "John W. Bischoff", "description": "American organist, singing-teacher, and song-writer"}],
    "place": {"name": "Chicago", "qualified_name": "Chicago, Illinois", "latitude": 41.8781, "longitude": -87.6298, "description": "City in Illinois"},
    "time": {"name": "1850", "date": "+1850-00-00T00:00:00Z", "precision": 9},
    "confidence": 0.90
  },
  {
    "summary": "John W. Bischoff worked as organist, singing-teacher, and song-writer in Washington from 1875.",
    "excerpt": "Bischoff, John W. (Chicago, 1850-1909, Washington), trained at the Wisconsin Institute for the Blind and in London, from 1875 was organist, singing-teacher and song-writer at Washington.",
    "people": [{"name": "John W. Bischoff", "description": "American organist, singing-teacher, and song-writer"}],
    "place": {"name": "Washington", "qualified_name": "Washington, D.C.", "latitude": 38.9072, "longitude": -77.0369, "description": "Capital of the United States"},
    "time": {"name": "1875", "date": "+1875-00-00T00:00:00Z", "precision": 9},
    "confidence": 0.90
  },
  {
    "summary": "John W. Bischoff died in Washington in 1909.",
    "excerpt": "Bischoff, John W. (Chicago, 1850-1909, Washington), trained at the Wisconsin Institute for the Blind and in London, from 1875 was organist, singing-teacher and song-writer at Washington.",
    "people": [{"name": "John W. Bischoff", "description": "American organist, singing-teacher, and song-writer"}],
    "place": {"name": "Washington", "qualified_name": "Washington, D.C.", "latitude": 38.9072, "longitude": -77.0369, "description": "Capital of the United States"},
    "time": {"name": "1909", "date": "+1909-00-00T00:00:00Z", "precision": 9},
    "confidence": 0.90
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

FIX_SUMMARIES_SYSTEM_PROMPT = """You are correcting historical event extractions. Each event has a "_missing" field listing entity names that do not appear verbatim in the summary.

For each input event, return one or more corrected replacement events in an inner array. Rules:

- If the problem is a missing name in the summary, rewrite the summary so all entity names in "_missing" appear as literal substrings. Preserve historical detail.
- If the time name is a date range (e.g. "1756-1762"), the event must be split into two events: one for the start date and one for the end date, each with a single-year time name that appears verbatim in its summary.
- Every output event must have its person name(s), place name, and time name as literal substrings of the summary.
- Remove "_missing" from all output events.

Return a JSON array of arrays — one inner array per input event, containing its replacement event(s):
[
  [{ corrected or split event }, ...],
  [{ corrected event }],
  ...
]

Return ONLY the JSON array of arrays, no other text."""


class ClaudeClient:
    def __init__(self, api_key: str, model: str = "haiku"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = MODEL_MAP.get(model, model)
        log.info(f"Using Claude model: {self._model}")

    def extract_events(
        self,
        chunk_text: str,
        source_title: str,
        source_author: str,
        start_page: int | None = None,
        end_page: int | None = None,
        _depth: int = 0,
    ) -> list[ExtractedEvent]:
        """Extract historical events from a text chunk.

        If the response is truncated (max_tokens hit), the chunk is split in half
        and each half is reprocessed recursively. Splitting stops at depth 2 (quarters
        of the original chunk) to bound API usage.
        """
        page_ctx = (
            f"pages {start_page}-{end_page}"
            if start_page is not None and end_page is not None
            else "unknown pages"
        )

        user_message = (
            f"Extract historical events from this passage of "
            f'"{source_title}" by {source_author}:\n\n{chunk_text}'
        )

        try:
            with self._client.messages.stream(
                model=self._model,
                max_tokens=32768,
                system=[
                    {
                        "type": "text",
                        "text": EXTRACTION_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()
        except anthropic.APIError as e:
            log.error(f"Claude API error during extraction [{page_ctx}]: {e}")
            return []

        if response.stop_reason == "max_tokens":
            if _depth < 2:
                log.warning(
                    f"Response truncated at depth {_depth} [{page_ctx}]; "
                    f"splitting chunk in half and reprocessing"
                )
                mid = len(chunk_text) // 2
                split_at = chunk_text.rfind("\n\n", 0, mid)
                if split_at == -1:
                    split_at = chunk_text.rfind("\n", 0, mid)
                if split_at == -1:
                    split_at = mid
                return self.extract_events(
                    chunk_text[:split_at], source_title, source_author,
                    start_page, end_page, _depth + 1,
                ) + self.extract_events(
                    chunk_text[split_at:], source_title, source_author,
                    start_page, end_page, _depth + 1,
                )
            log.warning(
                f"Response still truncated at depth 2 [{page_ctx}]; "
                f"parsing partial response — to retry, rerun with "
                f"--start-page {start_page} --end-page {end_page}"
            )

        valid, _ = self._parse_and_validate_events(
            response.content[0].text.strip(), start_page, end_page
        )
        return valid

    def _parse_and_validate_events(
        self,
        content: str,
        start_page: int | None,
        end_page: int | None,
        fix_inline: bool = True,
    ) -> tuple[list[ExtractedEvent], list[tuple[ExtractedEvent, list[str]]]]:
        """Parse a raw JSON response into validated ExtractedEvents.

        Returns (valid_events, invalid_events). When fix_inline=True the invalid
        events are fixed before returning and the second element is always empty.
        When fix_inline=False the invalid events are returned for the caller to
        handle (e.g. via a deferred batch fix).
        """
        page_ctx = (
            f"pages {start_page}-{end_page}"
            if start_page is not None and end_page is not None
            else "unknown pages"
        )

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
            log.error(
                f"Failed to parse Claude response as JSON [{page_ctx}] "
                f"— to retry: --start-page {start_page} --end-page {end_page}; "
                f"response prefix: {content[:200]}"
            )
            return [], []

        events = []
        for raw in raw_events:
            place_data = raw.get("place")
            time_data = raw.get("time")
            if not place_data:
                log.warning(
                    f"Skipping event with null place: {raw.get('summary', '')[:80]!r}"
                )
                continue
            if not time_data:
                log.warning(
                    f"Skipping event with null time: {raw.get('summary', '')[:80]!r}"
                )
                continue
            try:
                event = ExtractedEvent(
                    summary=raw["summary"],
                    excerpt=raw["excerpt"],
                    people=[ExtractedPerson(**p) for p in raw.get("people", [])],
                    place=ExtractedPlace(**place_data),
                    time=ExtractedTime(**time_data),
                    confidence=raw.get("confidence", 0.5),
                )
                events.append(event)
            except (KeyError, TypeError, ValueError) as e:
                log.warning(f"Skipping malformed event: {e}")
                continue

        valid: list[ExtractedEvent] = []
        to_fix: list[tuple[ExtractedEvent, list[str]]] = []
        for event in events:
            missing = self._validate_event(event)
            if missing:
                log.warning(f"Summary missing {missing!r}: {event.summary[:80]!r}")
                to_fix.append((event, missing))
            else:
                valid.append(event)

        if to_fix and fix_inline:
            log.info(f"Batch-fixing {len(to_fix)} events with invalid summaries")
            fixed_list = self._fix_summaries(to_fix)
            for (original, _), replacements in zip(to_fix, fixed_list):
                if not replacements:
                    log.warning(f"Could not fix summary, dropping: {original.summary[:80]!r}")
                    continue
                for fixed in replacements:
                    still_missing = self._validate_event(fixed)
                    if still_missing:
                        log.warning(f"Fixed event still missing {still_missing!r}, dropping: {fixed.summary[:80]!r}")
                    else:
                        valid.append(fixed)
            to_fix = []

        log.info(f"Extracted {len(valid)} events [{page_ctx}]")
        return valid, to_fix

    def submit_extraction_batch(
        self,
        chunks: list[tuple[str, int | None, int | None]],
        source_title: str,
        source_author: str,
    ) -> str:
        """Submit all chunks as a Message Batch. Returns the batch ID.

        Each tuple in chunks is (chunk_text, start_page, end_page).
        50% cost discount vs synchronous calls; results arrive asynchronously.
        """
        requests = []
        for i, (chunk_text, start_page, end_page) in enumerate(chunks):
            user_message = (
                f"Extract historical events from this passage of "
                f'"{source_title}" by {source_author}:\n\n{chunk_text}'
            )
            requests.append({
                "custom_id": f"chunk-{i:04d}-p{start_page}-{end_page}",
                "params": {
                    "model": self._model,
                    "max_tokens": 32768,
                    "system": [
                        {
                            "type": "text",
                            "text": EXTRACTION_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    "messages": [{"role": "user", "content": user_message}],
                },
            })

        batch = self._client.messages.batches.create(requests=requests)
        log.info(f"Submitted batch {batch.id} with {len(requests)} chunks")
        return batch.id

    def _fetch_batch_results_with_retry(
        self, batch_id: str, max_retries: int = 3
    ) -> list:
        """Fetch all batch results, retrying on network errors."""
        for attempt in range(max_retries):
            try:
                return list(self._client.messages.batches.results(batch_id))
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as e:
                if attempt < max_retries - 1:
                    wait = 5 * (2 ** attempt)
                    log.warning(
                        f"Batch results stream dropped ({e}); retrying in {wait}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait)
                else:
                    raise

    def poll_extraction_batch(
        self,
        batch_id: str,
        poll_interval: int = 60,
        fix_inline: bool = True,
    ) -> tuple[list[tuple[str, list[ExtractedEvent]]], list[tuple[ExtractedEvent, list[str]]]]:
        """Poll until the batch completes.

        Returns (chunk_results, all_invalid) where chunk_results is a list of
        (custom_id, valid_events) pairs in chunk order.

        When fix_inline=True (default), invalid events are fixed immediately and
        all_invalid is always empty. When fix_inline=False, invalid events are
        returned for the caller to handle via a deferred batch fix.
        """
        while True:
            status = self._client.messages.batches.retrieve(batch_id)
            counts = status.request_counts
            log.info(
                f"Batch {batch_id}: {status.processing_status} — "
                f"{counts.processing} processing, {counts.succeeded} succeeded, "
                f"{counts.errored} errored"
            )
            if status.processing_status == "ended":
                break
            time.sleep(poll_interval)

        all_invalid: list[tuple[ExtractedEvent, list[str]]] = []
        results = []
        for result in self._fetch_batch_results_with_retry(batch_id):
            custom_id = result.custom_id
            # Decode page range from custom_id: "chunk-0001-p5-10"
            try:
                page_part = custom_id.split("-p", 1)[1]
                start_str, _, end_str = page_part.partition("-")
                start_page: int | None = int(start_str)
                end_page: int | None = int(end_str)
            except (IndexError, ValueError):
                start_page = end_page = None

            if result.result.type == "succeeded":
                message = result.result.message
                if message.stop_reason == "max_tokens":
                    log.warning(
                        f"Batch chunk {custom_id} was truncated — "
                        f"to retry: --start-page {start_page} --end-page {end_page}"
                    )
                events, invalid = self._parse_and_validate_events(
                    message.content[0].text.strip(), start_page, end_page,
                    fix_inline=fix_inline,
                )
                # Stamp page_num on invalid events now so it survives through the fix batch
                for event, _ in invalid:
                    if event.page_num is None:
                        event.page_num = start_page
                all_invalid.extend(invalid)
            else:
                log.error(
                    f"Batch chunk {custom_id} failed ({result.result.type}) — "
                    f"to retry: --start-page {start_page} --end-page {end_page}"
                )
                events = []

            results.append((custom_id, events))

        results.sort(key=lambda x: x[0])
        return results, all_invalid

    def submit_fix_batch(
        self,
        invalid: list[tuple[ExtractedEvent, list[str]]],
    ) -> str:
        """Submit all invalid events as a Message Batch for fixing.

        Events are grouped into sub-requests of _FIX_BATCH_SIZE. Returns batch ID.
        """
        requests = []
        for batch_start in range(0, len(invalid), self._FIX_BATCH_SIZE):
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            payload = []
            for event, missing in batch:
                d = event.model_dump(mode="json")
                d["_missing"] = missing
                payload.append(d)
            user_message = (
                "Fix the events so every name listed in '_missing' appears verbatim "
                "in the summary. Split date-range events into separate events:\n\n"
                + json.dumps(payload, indent=2)
            )
            requests.append({
                "custom_id": f"fix-{batch_start:05d}",
                "params": {
                    "model": self._model,
                    "max_tokens": 16384,
                    "system": FIX_SUMMARIES_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
            })

        batch = self._client.messages.batches.create(requests=requests)
        log.info(f"Submitted fix batch {batch.id} with {len(requests)} sub-requests")
        return batch.id

    def poll_fix_batch(
        self,
        batch_id: str,
        invalid: list[tuple[ExtractedEvent, list[str]]],
        poll_interval: int = 60,
    ) -> list[list[ExtractedEvent]]:
        """Poll until the fix batch completes. Returns replacement lists parallel to invalid."""
        while True:
            status = self._client.messages.batches.retrieve(batch_id)
            counts = status.request_counts
            log.info(
                f"Fix batch {batch_id}: {status.processing_status} — "
                f"{counts.processing} processing, {counts.succeeded} succeeded, "
                f"{counts.errored} errored"
            )
            if status.processing_status == "ended":
                break
            time.sleep(poll_interval)

        # Collect by batch_start index
        batch_outputs: dict[int, list[list[ExtractedEvent]]] = {}
        for result in self._fetch_batch_results_with_retry(batch_id):
            batch_start = int(result.custom_id.split("-")[1])
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            if result.result.type == "succeeded":
                content = result.result.message.content[0].text.strip()
                batch_outputs[batch_start] = self._parse_fix_response(content, batch)
            else:
                log.error(f"Fix batch sub-request {result.custom_id} failed")
                batch_outputs[batch_start] = [[] for _ in batch]

        # Reassemble in original order
        results: list[list[ExtractedEvent]] = []
        for batch_start in range(0, len(invalid), self._FIX_BATCH_SIZE):
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            results.extend(batch_outputs.get(batch_start, [[] for _ in batch]))
        return results

    def _parse_fix_response(
        self,
        content: str,
        invalid: list[tuple[ExtractedEvent, list[str]]],
    ) -> list[list[ExtractedEvent]]:
        """Parse a fix-batch response into replacement event groups."""
        if content.startswith("```"):
            lines = content.split("\n")
            content = (
                "\n".join(lines[1:-1])
                if lines[-1].strip() == "```"
                else "\n".join(lines[1:])
            )

        try:
            raw_outer = json.loads(content)
        except json.JSONDecodeError:
            log.error(f"Failed to parse fix response: {content[:200]}")
            return [[] for _ in invalid]

        results: list[list[ExtractedEvent]] = []
        for i, (original, _) in enumerate(invalid):
            if i >= len(raw_outer):
                results.append([])
                continue
            raw_group = raw_outer[i]
            if not isinstance(raw_group, list):
                raw_group = [raw_group]
            group: list[ExtractedEvent] = []
            for raw in raw_group:
                raw.pop("_missing", None)
                try:
                    group.append(ExtractedEvent(
                        summary=raw["summary"],
                        excerpt=raw.get("excerpt", original.excerpt),
                        people=[ExtractedPerson(**p) for p in raw.get("people", [])],
                        place=ExtractedPlace(**raw["place"]),
                        time=ExtractedTime(**raw["time"]),
                        confidence=raw.get("confidence", original.confidence),
                        page_num=original.page_num,
                    ))
                except (KeyError, TypeError, ValueError) as e:
                    log.warning(f"Skipping malformed fixed event: {e}")
            results.append(group)
        return results

    def _validate_event(self, event: ExtractedEvent) -> list[str]:
        """Return entity names that are not present as verbatim substrings in the summary."""
        missing = []
        for person in event.people:
            if person.name not in event.summary:
                missing.append(person.name)
        if event.place.name not in event.summary:
            missing.append(event.place.name)
        if event.time.name not in event.summary:
            missing.append(event.time.name)
        return missing

    _FIX_BATCH_SIZE = 15

    def _fix_summaries(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Batch-send events with invalid summaries to Claude for correction.

        Returns a list of replacement lists — one per input event. An event may be
        replaced by multiple events (e.g. when a date range is split into two).
        An empty inner list means the event could not be fixed and should be dropped.

        Events are processed in batches of _FIX_BATCH_SIZE to keep output tokens
        manageable and avoid truncation.
        """
        results: list[list[ExtractedEvent]] = []
        for batch_start in range(0, len(invalid), self._FIX_BATCH_SIZE):
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            results.extend(self._fix_summaries_batch(batch))
        return results

    def _fix_summaries_batch(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Fix a single batch of invalid events."""
        payload = []
        for event, missing in invalid:
            d = event.model_dump(mode="json")
            d["_missing"] = missing
            payload.append(d)

        user_message = (
            "Fix the events so every name listed in '_missing' appears verbatim "
            "in the summary. Split date-range events into separate events:\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            with self._client.messages.stream(
                model=self._model,
                max_tokens=16384,
                system=FIX_SUMMARIES_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()
        except anthropic.APIError as e:
            log.error(f"Claude API error during summary fix: {e}")
            return [[] for _ in invalid]

        if response.stop_reason == "max_tokens":
            log.warning(
                f"Summary fix response truncated for batch of {len(invalid)} events; "
                f"all will be dropped"
            )
            return [[] for _ in invalid]

        return self._parse_fix_response(response.content[0].text.strip(), invalid)

    def pick_best_entity_match(
        self,
        entity_name: str,
        entity_type: str,
        candidates: list[dict],
    ) -> UUID | None:
        """Use Claude to pick the best matching entity from candidates."""
        if not candidates:
            return None

        def _fmt_candidate(c: dict) -> str:
            parts = [f"- id: {c['id']}, name: {c['name']}"]
            if c.get("description"):
                parts.append(f"  description: {c['description']}")
            if c.get("earliest_date") or c.get("latest_date"):
                parts.append(
                    f"  dates: {c.get('earliest_date', '?')} – {c.get('latest_date', '?')}"
                )
            return "\n".join(parts)

        candidates_text = "\n".join(_fmt_candidate(c) for c in candidates)

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
            result, _ = json.JSONDecoder().raw_decode(content)
            if result.get("match") and result.get("id"):
                return UUID(result["id"])
        except (json.JSONDecodeError, ValueError) as e:
            log.warning(f"Failed to parse entity match response: {e}")

        return None
