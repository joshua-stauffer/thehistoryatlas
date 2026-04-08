import json
import logging
import time
from uuid import UUID

import anthropic
import httpx

from text_reader.base_client import (
    ENTITY_MATCH_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    FIX_SUMMARIES_SYSTEM_PROMPT,
    MODEL_MAP,
    MODEL_PRICING,
    BaseLLMClient,
)

# Re-export for backwards compatibility (used by tests)
__all__ = ["ClaudeClient", "MODEL_MAP"]
from text_reader.types import (
    ExtractedEvent,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedTime,
)

log = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    def __init__(
        self, api_key: str, model: str = "sonnet", secondary_model: str = "sonnet"
    ):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = MODEL_MAP.get(model, model)
        self._secondary_model = MODEL_MAP.get(secondary_model, secondary_model)
        log.info(
            f"Using Claude model: {self._model} (secondary: {self._secondary_model})"
        )
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
                    chunk_text[:split_at],
                    source_title,
                    source_author,
                    start_page,
                    end_page,
                    _depth + 1,
                ) + self.extract_events(
                    chunk_text[split_at:],
                    source_title,
                    source_author,
                    start_page,
                    end_page,
                    _depth + 1,
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
            requests.append(
                {
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
                }
            )

        batch = self._client.messages.batches.create(requests=requests)
        log.info(f"Submitted batch {batch.id} with {len(requests)} chunks")
        return batch.id

    def poll_extraction_batch(
        self,
        batch_id: str,
        poll_interval: int = 60,
        fix_inline: bool = True,
    ) -> tuple[
        list[tuple[str, list[ExtractedEvent]]], list[tuple[ExtractedEvent, list[str]]]
    ]:
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
                    message.content[0].text.strip(),
                    start_page,
                    end_page,
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
            requests.append(
                {
                    "custom_id": f"fix-{batch_start:05d}",
                    "params": {
                        "model": self._secondary_model,
                        "max_tokens": 16384,
                        "system": FIX_SUMMARIES_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                }
            )

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

    def _fix_summaries_batch(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Fix a single batch of invalid events (synchronous via API)."""
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
                model=self._secondary_model,
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
            requests.append(
                {
                    "custom_id": req["key"],
                    "params": {
                        "model": self._secondary_model,
                        "max_tokens": 256,
                        "system": ENTITY_MATCH_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                }
            )

        batch = self._client.messages.batches.create(requests=requests)
        log.info(
            f"Submitted entity match batch {batch.id} with {len(requests)} requests"
        )
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
                model=self._secondary_model,
                max_tokens=256,
                system=ENTITY_MATCH_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": "{"},
                ],
            )
        except anthropic.APIError as e:
            log.error(f"Claude API error during entity matching: {e}")
            return None

        self._track_usage(response.usage, batch=False)
        return self._parse_entity_match_result(response.content[0].text.strip())

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _fetch_batch_results_with_retry(
        self, batch_id: str, max_retries: int = 3
    ) -> list:
        """Fetch all batch results, retrying on network errors."""
        for attempt in range(max_retries):
            try:
                return list(self._client.messages.batches.results(batch_id))
            except (
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ConnectError,
            ) as e:
                if attempt < max_retries - 1:
                    wait = 5 * (2**attempt)
                    log.warning(
                        f"Batch results stream dropped ({e}); retrying in {wait}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait)
                else:
                    raise
