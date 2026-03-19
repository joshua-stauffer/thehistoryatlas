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

# (input_price_per_1M, output_price_per_1M) in USD
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-6": (15.00, 75.00),
}

EXTRACTION_SYSTEM_PROMPT = """You are a scholarly research assistant specializing in historical text analysis. Your job is to extract structured historical events from source texts.

A single passage may yield multiple events — extract each discrete occurrence separately. Biographical entries commonly contain several distinct events: a birth, a death, career appointments, performances, relocations, publications, and so on. Extract all of them.

For each distinct historical event described in the text, extract:

1. **Summary**: One or two sentences describing the event, written in third person past tense, using natural language. The summary MUST contain the primary person's full name, the place `name` (as defined below), and the time `name` as literal substrings — these will be used to locate tags in the text.

   **Enrich each summary** by weaving in a contextual detail from the source text that answers one of these questions:
   - What circumstances surrounded this event? (e.g., war, illness, patronage, rivalry, exile)
   - What stage of the person's life or career was this? (e.g., debut, peak fame, late career, childhood)
   - What was the significance or reception? (e.g., acclaim, controversy, landmark achievement)
   - What was the consequence or outcome? (e.g., new appointment, health decline, lasting influence)

   Prefer weaving the enrichment into the main sentence as a phrase or clause. Use a second sentence only when the enrichment doesn't fit naturally inline. Examples:
   - GOOD (inline): "Felix Mendelssohn, at the height of his fame, conducted the premiere of his oratorio Elijah to thunderous acclaim at the Birmingham Festival on August 26, 1846."
   - GOOD (two sentences): "The outbreak of war caught Benjamin James Dale in Germany, where he was interned at Ruhleben in 1914. He remained imprisoned until March 1918, when he was exchanged and removed to Holland, returning home just before the Armistice with his health gravely impaired."
   - TOO BARE: "Felix Mendelssohn conducted Elijah in Birmingham in 1846."

   **Enrichment boundaries**: Contextual detail should not introduce *other specific places or dates* that deserve their own events. If the context naturally references a different time or place (e.g., a death date, a prior city), extract that as a separate event instead. For example:
   - GOOD: "Thomas Norris was engaged at the Birmingham Festival in 1790, but the effort proved fatal and he expired ten days later." (The death is a separate event.)
   - BAD: "Thomas Norris was engaged at the Birmingham Festival in 1790, and he expired ten days later at Himley Hall near Stourbridge on Sept. 3, 1790." (The death's date and place belong in their own event.)
   - GOOD: "Thomas Norris was appointed organist of Christ Church Cathedral in Oxford in 1765, marking the beginning of a long association with the university city." (The vague reference to the future is fine — it's not a concrete second event.)
   - BORDERLINE BUT OK: "Carl Friedrich Ludwig Nohl returned to Berlin in 1857 after his health had necessitated a journey to France and Italy." (France and Italy are mentioned only as vague context, not as concrete events.)

   **CRITICAL — full names in every summary**: The primary subject of each event MUST be referred to by their FULL name (exactly as given in the `people` array). Write "Felix Mendelssohn conducted..." not "Mendelssohn conducted...". Write "George Frideric Handel composed..." not "Handel composed...". Each summary is processed independently — there is no prior context, so the full name must always appear. This is the single most common extraction error.

   **Other people mentioned in the summary** may use whatever name form is natural — full name, surname only, or any commonly used variant. For example: "Bellini's opera Norma, with words by Romani, was produced at Milan on Dec. 26, 1831, with Donzelli, Pasta, and Grisi in the cast." Here "Romani", "Donzelli", "Pasta", and "Grisi" are acceptable name forms, and each should appear in the `people` array with their full name and a description.

   **CRITICAL — the time `name` must appear verbatim in the summary**: Write the date in the summary exactly as you set time.name. If time.name is "March 1834", the summary must contain the substring "March 1834". Never write a date range in the summary (e.g. "May 18-20" or "June 7-9" or "February and March" or "1885-92") — use only the single date from time.name.

   **CRITICAL — the place `name` must appear verbatim in the summary**: Every event happens somewhere. Even if the source text implies the location from context, state it explicitly in the summary. Biographical entries often mention a city once in the header (e.g., "Dale, Benjamin James, b. London, 1885") and then list achievements without repeating it. You must still weave the place name into every summary derived from that entry.

2. **People**: Every named person who appears in the summary text. This includes the primary subject AND any other people mentioned — collaborators, librettists, performers, dedicatees, patrons, teachers, etc.
   - The primary subject's name in the `people` array must exactly match how their full name appears in the summary.
   - For other people who appear by surname only in the summary, still provide their **full name** and description in the `people` array. The `name` field should be the form used in the summary (e.g., "Romani"), but add a `full_name` field with the complete name (e.g., "Felice Romani"). If you don't know the full name, omit `full_name`.
   - Include:
     - name: The name as it appears in the summary text (must be a verbatim substring of the summary)
     - full_name: The person's full name, if different from `name` (optional — omit if `name` is already the full name)
     - description: Brief identifying description (e.g., "Italian librettist", "English soprano")

3. **Place**: The location where the event occurred. Include:
   - name: The place name exactly as you write it in the summary — use natural, concise language (e.g. "New York", "Boston", "Paris"). This must match the summary verbatim.
   - qualified_name: The fully qualified name for disambiguation, including state or country. Spell out abbreviations (Pa. -> Pennsylvania, N.Y. -> New York, Mass. -> Massachusetts, etc.). Examples: "New York, New York"; "Boston, Massachusetts"; "Ephrata, Pennsylvania"; "Leipzig, Germany". If the source gives a qualifier (e.g. "Ephrata, Pa."), always populate this field.
   - latitude/longitude: Approximate coordinates if you can determine them (null if unknown)
   - description: Brief description

4. **Time**: When the event occurred. Include:
   - name: Human-readable date (e.g., "1759", "March 1685", "14 June 1770"). Never use seasonal terms ("Spring 1834") — use the month or year instead. Never use a date range. Never use vague period descriptions ("first quarter of the 16th century") — use the best available specific year instead.
   - date: ISO-8601 formatted with leading +/- (e.g., "+1759-00-00T00:00:00Z", "+1685-03-00T00:00:00Z")
   - precision: 9 for year, 10 for month, 11 for day
   - calendar_model: "http://www.wikidata.org/entity/Q1985727" (Gregorian)

5. **Excerpt**: The verbatim sentence or short passage from the source text that supports this event. Copy it exactly as it appears in the source — do not paraphrase or summarize.

6. **Confidence**: A score from 0.0 to 1.0 indicating how confident you are in the extraction accuracy.

Valid event types include (but are not limited to):
- Births, deaths, and relocations
- Career appointments, performances, teaching positions
- Publications: books, dictionaries, journals, sheet music — these are historical events. For a publication, the author or editor is the person; for example, "Waldo Selden Pratt edited Grove's Dictionary American Supplement in New York in November 1920" not "The Macmillan Company published...". Do not use a publishing house or organization as the person.
- Compositions, premieres, and recordings
- Instrument-making and manufacturing (e.g., a craftsman building the first piano of a type in a city)
- Institutional founding (conservatories, orchestras, music schools) — use the founder as the person

Rules:
- Only extract events with concrete individual people, places, AND times. Skip truly vague references with no specific date or location. Organizations and publishers are not acceptable substitutes for a named person.
- The summary must contain the primary person's full name, the `place.name` value, and the `time.name` value as exact literal substrings. The `place.name` should be whatever natural form you used in the sentence (e.g. "New York", "Boston") — not the qualified form. The `place.qualified_name` is for disambiguation only and does not need to appear in the summary.
- Every person name in the `people` array must appear as a verbatim substring in the summary.
- Use the most specific date precision available (day > month > year).
- For BCE dates, use negative years (e.g., "-0500-00-00T00:00:00Z").
- Each event must have a single, discrete point in time — never a range. Any time span must be split into separate events for the start and end:
  - Multi-day: "June 7-9, 1835" -> one event for "June 7, 1835" (start) and one for "June 9, 1835" (end)
  - Multi-month: "February and March 1838" -> one event for "February 1838" and one for "March 1838"
  - Multi-year: "1885-92" -> one event for "1885" and one for "1892"
  The time name must always be a single year, month, or day.
- Birth and death dates with locations (e.g., "b. Chicago, 1850" or "d. Paris, 1903") are valid events — extract them.
- Extract every qualifying event present in the passage, even if the passage is primarily a preface, table of contents, or bibliography. Do not skip a chunk just because most of it is vague — extract whatever specific events are present.

**Self-check before returning**: For each event, verify that:
1. The primary person's full name appears as a literal substring of the summary
2. Every person `name` in the people array appears as a literal substring of the summary
3. The place name appears as a literal substring of the summary
4. The time name appears as a literal substring of the summary
5. The time name is a single specific date (not a range, not a season, not a vague period)
If any check fails, rewrite the summary (or adjust the names) before returning.

Return a JSON array of events. Example:
```json
[
  {
    "summary": "Bellini's opera Norma, with words by Romani, was produced at Milan on Dec. 26, 1831, with Donzelli, Pasta, and Grisi in the cast.",
    "excerpt": "Norma. Opera in two acts; words by Romani, music by Bellini. Produced at Milan, December 26, 1831, with Donzelli, Pasta, and Grisi.",
    "people": [
      {"name": "Bellini", "full_name": "Vincenzo Bellini", "description": "Italian opera composer"},
      {"name": "Romani", "full_name": "Felice Romani", "description": "Italian librettist"},
      {"name": "Donzelli", "full_name": "Domenico Donzelli", "description": "Italian tenor"},
      {"name": "Pasta", "full_name": "Giuditta Pasta", "description": "Italian soprano"},
      {"name": "Grisi", "full_name": "Giulia Grisi", "description": "Italian soprano"}
    ],
    "place": {"name": "Milan", "qualified_name": "Milan, Italy", "latitude": 45.4642, "longitude": 9.1900, "description": "City in northern Italy"},
    "time": {"name": "Dec. 26, 1831", "date": "+1831-12-26T00:00:00Z", "precision": 11},
    "confidence": 0.95
  }
]
```

Return ONLY the JSON array, no other text."""

ENTITY_MATCH_SYSTEM_PROMPT = """You are helping match extracted historical entities to existing database records.

Given an entity name, type, context, and a list of candidate matches from the database, determine if any candidate is the same entity. Consider:
- Name variations, historical spelling differences, and alternative forms
- Historical and geographic context: if the context indicates a specific nationality or region (e.g. "Italian composer"), strongly prefer candidates from that country or region (e.g. Florence, Italy over Florence, Nebraska)
- Description match: nationalities, roles, time periods

If no candidate is a confident match given the context, return no match — do not force a match when the context contradicts the candidate.

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
    _FIX_BATCH_SIZE = 15

    def __init__(self, api_key: str, model: str = "sonnet"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = MODEL_MAP.get(model, model)
        log.info(f"Using Claude model: {self._model}")
        # Token usage accumulators (batch vs standard rate separate)
        self._batch_input_tokens = 0
        self._batch_output_tokens = 0
        self._standard_input_tokens = 0
        self._standard_output_tokens = 0

    def total_cost(self) -> float:
        """Return total USD cost based on accumulated token usage."""
        input_price, output_price = MODEL_PRICING.get(self._model, (3.00, 15.00))
        standard = (
            self._standard_input_tokens * input_price
            + self._standard_output_tokens * output_price
        ) / 1_000_000
        batch = (
            self._batch_input_tokens * input_price * 0.5
            + self._batch_output_tokens * output_price * 0.5
        ) / 1_000_000
        return standard + batch

    def _track_usage(self, usage, batch: bool = False) -> None:
        if batch:
            self._batch_input_tokens += usage.input_tokens
            self._batch_output_tokens += usage.output_tokens
        else:
            self._standard_input_tokens += usage.input_tokens
            self._standard_output_tokens += usage.output_tokens

    # -------------------------------------------------------------------------
    # Extraction
    # -------------------------------------------------------------------------

    def extract_events(
        self,
        chunk_text: str,
        source_title: str,
        source_author: str,
        start_page: int | None = None,
        end_page: int | None = None,
        _depth: int = 0,
    ) -> list[ExtractedEvent]:
        """Extract historical events from a text chunk (synchronous, non-batch)."""
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

        self._track_usage(response.usage, batch=False)

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

    def submit_extraction_batch(
        self,
        chunks: list[tuple[str, int | None, int | None]],
        source_title: str,
        source_author: str,
    ) -> str:
        """Submit all chunks as a Message Batch. Returns the batch ID."""
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

    def poll_extraction_batch(
        self,
        batch_id: str,
        poll_interval: int = 60,
        fix_inline: bool = True,
    ) -> tuple[list[tuple[str, list[ExtractedEvent]]], list[tuple[ExtractedEvent, list[str]]]]:
        """Poll until the extraction batch completes.

        Returns (chunk_results, all_invalid). When fix_inline=False, invalid
        events are returned for the caller to handle via a deferred batch fix.
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
            try:
                page_part = custom_id.split("-p", 1)[1]
                start_str, _, end_str = page_part.partition("-")
                start_page: int | None = int(start_str)
                end_page: int | None = int(end_str)
            except (IndexError, ValueError):
                start_page = end_page = None

            if result.result.type == "succeeded":
                message = result.result.message
                self._track_usage(message.usage, batch=True)
                if message.stop_reason == "max_tokens":
                    log.warning(
                        f"Batch chunk {custom_id} was truncated — "
                        f"to retry: --start-page {start_page} --end-page {end_page}"
                    )
                events, invalid = self._parse_and_validate_events(
                    message.content[0].text.strip(), start_page, end_page,
                    fix_inline=fix_inline,
                )
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

    # -------------------------------------------------------------------------
    # Fix batch
    # -------------------------------------------------------------------------

    def submit_fix_batch(
        self,
        invalid: list[tuple[ExtractedEvent, list[str]]],
    ) -> str:
        """Submit all invalid events as a Message Batch for fixing."""
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

        batch_outputs: dict[int, list[list[ExtractedEvent]]] = {}
        for result in self._fetch_batch_results_with_retry(batch_id):
            batch_start = int(result.custom_id.split("-")[1])
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            if result.result.type == "succeeded":
                self._track_usage(result.result.message.usage, batch=True)
                content = result.result.message.content[0].text.strip()
                batch_outputs[batch_start] = self._parse_fix_response(content, batch)
            else:
                log.error(f"Fix batch sub-request {result.custom_id} failed")
                batch_outputs[batch_start] = [[] for _ in batch]

        results: list[list[ExtractedEvent]] = []
        for batch_start in range(0, len(invalid), self._FIX_BATCH_SIZE):
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            results.extend(batch_outputs.get(batch_start, [[] for _ in batch]))
        return results

    # -------------------------------------------------------------------------
    # Entity match batch
    # -------------------------------------------------------------------------

    def submit_entity_match_batch(self, entity_requests: list[dict]) -> str:
        """Submit all entity-matching decisions as a single Message Batch.

        entity_requests: list of dicts with keys:
          key (str), entity_name (str), entity_type (str),
          context (str | None), candidates (list[dict])

        Returns the batch ID.
        """
        requests = []
        for req in entity_requests:
            user_message = self._build_entity_match_message(
                req["entity_name"],
                req["entity_type"],
                req["candidates"],
                req.get("context"),
            )
            requests.append({
                "custom_id": req["key"],
                "params": {
                    "model": self._model,
                    "max_tokens": 256,
                    "system": ENTITY_MATCH_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
            })

        batch = self._client.messages.batches.create(requests=requests)
        log.info(f"Submitted entity match batch {batch.id} with {len(requests)} requests")
        return batch.id

    def poll_entity_match_batch(
        self,
        batch_id: str,
        poll_interval: int = 30,
    ) -> dict[str, UUID | None]:
        """Poll until the entity match batch completes.

        Returns a dict mapping custom_id → matched UUID (or None if no match).
        """
        while True:
            status = self._client.messages.batches.retrieve(batch_id)
            counts = status.request_counts
            log.info(
                f"Entity match batch {batch_id}: {status.processing_status} — "
                f"{counts.processing} processing, {counts.succeeded} succeeded, "
                f"{counts.errored} errored"
            )
            if status.processing_status == "ended":
                break
            time.sleep(poll_interval)

        results: dict[str, UUID | None] = {}
        for result in self._fetch_batch_results_with_retry(batch_id):
            key = result.custom_id
            if result.result.type == "succeeded":
                self._track_usage(result.result.message.usage, batch=True)
                content = result.result.message.content[0].text.strip()
                results[key] = self._parse_entity_match_result(content, key)
            else:
                log.warning(f"Entity match batch request {key} failed")
                results[key] = None
        return results

    def pick_best_entity_match(
        self,
        entity_name: str,
        entity_type: str,
        candidates: list[dict],
        context: str | None = None,
    ) -> UUID | None:
        """Use Claude to pick the best matching entity from candidates (synchronous).

        context: optional string describing the historical/geographic context
        to help Claude disambiguate between candidates from different regions.
        """
        if not candidates:
            return None

        user_message = self._build_entity_match_message(
            entity_name, entity_type, candidates, context
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

        self._track_usage(response.usage, batch=False)
        return self._parse_entity_match_result(response.content[0].text.strip())

    # -------------------------------------------------------------------------
    # Shared helpers
    # -------------------------------------------------------------------------

    def _build_entity_match_message(
        self,
        entity_name: str,
        entity_type: str,
        candidates: list[dict],
        context: str | None = None,
    ) -> str:
        candidates_text = "\n".join(self._fmt_candidate(c) for c in candidates)
        msg = f"Entity to match:\n- Name: {entity_name}\n- Type: {entity_type}\n"
        if context:
            msg += f"- Context: {context}\n"
        msg += f"\nCandidates:\n{candidates_text}"
        return msg

    def _fmt_candidate(self, c: dict) -> str:
        parts = [f"- id: {c['id']}, name: {c['name']}"]
        if c.get("description"):
            parts.append(f"  description: {c['description']}")
        if c.get("earliest_date") or c.get("latest_date"):
            parts.append(
                f"  dates: {c.get('earliest_date', '?')} – {c.get('latest_date', '?')}"
            )
        return "\n".join(parts)

    def _parse_entity_match_result(self, content: str, key: str = "?") -> UUID | None:
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
            log.warning(
                f"Failed to parse entity match response [{key}]: {e}; "
                f"content={content[:120]!r}"
            )
        return None

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

    def _parse_and_validate_events(
        self,
        content: str,
        start_page: int | None,
        end_page: int | None,
        fix_inline: bool = True,
    ) -> tuple[list[ExtractedEvent], list[tuple[ExtractedEvent, list[str]]]]:
        """Parse a raw JSON response into validated ExtractedEvents."""
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

    def _validate_event(self, event: ExtractedEvent) -> list[str]:
        """Return entity names not present as verbatim substrings in the summary."""
        missing = []
        for person in event.people:
            if person.name not in event.summary:
                missing.append(person.name)
        if event.place.name not in event.summary:
            missing.append(event.place.name)
        if event.time.name not in event.summary:
            missing.append(event.time.name)
        return missing

    def _fix_summaries(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Batch-send events with invalid summaries to Claude for correction."""
        results: list[list[ExtractedEvent]] = []
        for batch_start in range(0, len(invalid), self._FIX_BATCH_SIZE):
            batch = invalid[batch_start : batch_start + self._FIX_BATCH_SIZE]
            results.extend(self._fix_summaries_batch(batch))
        return results

    def _fix_summaries_batch(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Fix a single batch of invalid events (synchronous)."""
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

        self._track_usage(response.usage, batch=False)

        if response.stop_reason == "max_tokens":
            log.warning(
                f"Summary fix response truncated for batch of {len(invalid)} events; "
                f"all will be dropped"
            )
            return [[] for _ in invalid]

        return self._parse_fix_response(response.content[0].text.strip(), invalid)

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
