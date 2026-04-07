"""LLM client that uses the Claude Code CLI (claude -p) as the backend."""

import json
import logging
import subprocess
from uuid import UUID

from text_reader.base_client import (
    ENTITY_MATCH_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    FIX_SUMMARIES_SYSTEM_PROMPT,
    MODEL_MAP,
    BaseLLMClient,
)
from text_reader.types import ExtractedEvent

log = logging.getLogger(__name__)


class ClaudeCodeClient(BaseLLMClient):
    """LLM client that invokes the `claude` CLI for each request."""

    def __init__(self, model: str = "sonnet"):
        self._model = MODEL_MAP.get(model, model)
        self._total_cost = 0.0
        log.info(f"Using Claude Code CLI with model: {self._model}")

    def _call_claude(self, system_prompt: str, user_message: str) -> str:
        """Invoke ``claude -p`` and return the response text.

        Uses ``--output-format json`` so we can extract both the result text
        and the cost reported by Claude Code.
        """
        cmd = [
            "claude",
            "-p",
            "--model",
            self._model,
            "--output-format",
            "json",
            "-s",
            system_prompt,
        ]
        log.debug(f"Running: {' '.join(cmd[:6])}... (input {len(user_message)} chars)")

        result = subprocess.run(
            cmd,
            input=user_message,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            log.error(
                f"Claude Code exited with code {result.returncode}: "
                f"{result.stderr[:500]}"
            )
            raise RuntimeError(
                f"Claude Code exited with code {result.returncode}: "
                f"{result.stderr[:200]}"
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fall back to treating stdout as plain text (e.g. older CLI version)
            log.debug("Could not parse JSON output; using raw stdout")
            return result.stdout.strip()

        self._total_cost += data.get("cost_usd", 0.0)
        return data.get("result", result.stdout).strip()

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
        """Extract historical events from a text chunk via Claude Code CLI."""
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
            content = self._call_claude(EXTRACTION_SYSTEM_PROMPT, user_message)
        except RuntimeError as e:
            log.error(f"Claude Code error during extraction [{page_ctx}]: {e}")
            return []

        valid, _ = self._parse_and_validate_events(content, start_page, end_page)
        return valid

    # -------------------------------------------------------------------------
    # Fix summaries (synchronous via CLI)
    # -------------------------------------------------------------------------

    def _fix_summaries_batch(
        self, invalid: list[tuple[ExtractedEvent, list[str]]]
    ) -> list[list[ExtractedEvent]]:
        """Fix a single batch of invalid events via Claude Code CLI."""
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
            content = self._call_claude(FIX_SUMMARIES_SYSTEM_PROMPT, user_message)
        except RuntimeError as e:
            log.error(f"Claude Code error during summary fix: {e}")
            return [[] for _ in invalid]

        return self._parse_fix_response(content, invalid)

    # -------------------------------------------------------------------------
    # Entity matching (synchronous via CLI)
    # -------------------------------------------------------------------------

    def pick_best_entity_match(
        self,
        entity_name: str,
        entity_type: str,
        candidates: list[dict],
        context: str | None = None,
    ) -> UUID | None:
        """Use Claude Code CLI to pick the best matching entity from candidates."""
        if not candidates:
            return None

        user_message = self._build_entity_match_message(
            entity_name, entity_type, candidates, context
        )

        try:
            content = self._call_claude(ENTITY_MATCH_SYSTEM_PROMPT, user_message)
        except RuntimeError as e:
            log.error(f"Claude Code error during entity matching: {e}")
            return None

        return self._parse_entity_match_result(content)

    # -------------------------------------------------------------------------
    # Cost
    # -------------------------------------------------------------------------

    def total_cost(self) -> float:
        """Return total USD cost as reported by Claude Code CLI."""
        return self._total_cost
