"""LLM client that uses the Claude Code CLI (claude -p) as the backend."""

import json
import logging
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
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

_QUOTA_KEYWORDS = re.compile(
    r"rate.?limit|quota|usage.?limit|hit.*limit|exceeded|overloaded|too many requests|429",
    re.IGNORECASE,
)


def _parse_reset_time(error_msg: str) -> datetime | None:
    """Try to extract a quota-reset timestamp from an error message.

    Handles:
      - ISO 8601:  2026-04-08T03:00:00Z  /  2026-04-08T03:00:00+00:00
      - RFC 3339 without T:  2026-04-08 03:00:00
      - Relative:  "in 30 minutes", "in 2 hours"
      - Clock:     "at 3:00 AM", "at 15:00"
    """
    # ISO / RFC 3339 timestamp
    m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[Z+\-][\d:]*)?", error_msg)
    if m:
        raw = m.group().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass

    # Relative: "in N minutes/hours"
    m = re.search(r"in\s+(\d+)\s*(minute|min|hour|hr)s?", error_msg, re.IGNORECASE)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        delta = (
            timedelta(hours=amount)
            if unit.startswith("h")
            else timedelta(minutes=amount)
        )
        return datetime.now(timezone.utc) + delta

    # Clock time: "at HH:MM AM/PM" or "at HH:MM"
    m = re.search(r"at\s+(\d{1,2}):(\d{2})\s*(AM|PM)?", error_msg, re.IGNORECASE)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        ampm = (m.group(3) or "").upper()
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
        target = datetime.now().replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        if target <= datetime.now():
            target += timedelta(days=1)
        return target

    # Bare hour: "resets 2am", "resets 2am (Europe/Zurich)", "resets 3 PM"
    m = re.search(
        r"resets?\s+(\d{1,2})\s*(am|pm)(?:\s*\(([^)]+)\))?",
        error_msg,
        re.IGNORECASE,
    )
    if m:
        hour = int(m.group(1))
        ampm = m.group(2).upper()
        tz_name = m.group(3)
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
        # Use the timezone from the error message if available
        try:
            tz = ZoneInfo(tz_name) if tz_name else None
        except KeyError:
            tz = None
        now = datetime.now(tz) if tz else datetime.now()
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    return None


class ClaudeCodeClient(BaseLLMClient):
    """LLM client that invokes the `claude` CLI for each request."""

    _MAX_RETRIES = 30
    _POLL_INTERVAL = 900  # 15 minutes

    def __init__(self, model: str = "sonnet", secondary_model: str = "sonnet"):
        self._model = MODEL_MAP.get(model, model)
        self._secondary_model = MODEL_MAP.get(secondary_model, secondary_model)
        self._total_cost = 0.0
        log.info(
            f"Using Claude Code CLI with model: {self._model} "
            f"(secondary: {self._secondary_model})"
        )

    def _call_claude(
        self, system_prompt: str, user_message: str, model: str | None = None
    ) -> str:
        """Invoke ``claude -p`` and return the response text.

        Uses ``--output-format json`` so we can extract both the result text
        and the cost reported by Claude Code.  If a quota / rate-limit error
        is detected the method sleeps until the reset time (or uses
        exponential back-off) and retries automatically.
        """
        cmd = [
            "claude",
            "-p",
            "--tools",
            "",
            "--model",
            model or self._model,
            "--output-format",
            "json",
            "--system-prompt",
            system_prompt,
        ]

        for attempt in range(1, self._MAX_RETRIES + 1):
            log.debug(
                f"Running: {' '.join(cmd[:8])}... "
                f"(input {len(user_message)} chars, attempt {attempt})"
            )

            result = subprocess.run(
                cmd,
                input=user_message,
                capture_output=True,
                text=True,
            )

            # Try to parse JSON regardless of exit code — quota errors
            # come back as exit 1 with valid JSON on stdout.
            data = None
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                pass

            # Check for quota / rate-limit errors
            if data and data.get("is_error"):
                error_msg = data.get("result", "")
                if _QUOTA_KEYWORDS.search(error_msg):
                    wait = self._quota_wait(error_msg, attempt)
                    log.warning(
                        f"Quota/rate-limit hit (attempt {attempt}/{self._MAX_RETRIES}): "
                        f"{error_msg[:200]}"
                    )
                    print(
                        f"\nQuota/rate-limit hit. "
                        f"Waiting {wait // 60:.0f}m {wait % 60:.0f}s before retry. "
                        f"(Ctrl+C to quit — progress is saved.)"
                    )
                    time.sleep(wait)
                    continue
                # Non-quota error with is_error — raise
                raise RuntimeError(f"Claude Code error: {error_msg[:200]}")

            # Non-JSON or non-quota failure
            if result.returncode != 0:
                error_detail = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(
                    f"Claude Code exited with code {result.returncode}: "
                    f"{error_detail[:200]}"
                )

            # Success
            if data:
                self._total_cost += data.get("cost_usd", 0) or data.get(
                    "total_cost_usd", 0
                )
                return data.get("result", result.stdout).strip()
            return result.stdout.strip()

        raise RuntimeError(
            f"Claude Code: max retries ({self._MAX_RETRIES}) exceeded due to quota limits"
        )

    @staticmethod
    def _quota_wait(error_msg: str, attempt: int) -> float:
        """Return seconds to sleep before retrying a quota error."""
        reset = _parse_reset_time(error_msg)
        if reset is not None:
            now = datetime.now(timezone.utc)
            # Make reset offset-aware if it isn't already
            if reset.tzinfo is None:
                reset = reset.replace(tzinfo=timezone.utc)
            wait = (reset - now).total_seconds() + 60  # 1-minute buffer
            if wait > 0:
                return wait
        # Fallback: fixed polling interval
        return ClaudeCodeClient._POLL_INTERVAL

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
    ) -> list[ExtractedEvent] | None:
        """Extract historical events from a text chunk via Claude Code CLI.

        Returns None if extraction failed (parse error, runtime error) vs
        an empty list if extraction succeeded but found no events.
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
            content = self._call_claude(EXTRACTION_SYSTEM_PROMPT, user_message)
        except RuntimeError as e:
            log.error(f"Claude Code error during extraction [{page_ctx}]: {e}")
            return None

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
            content = self._call_claude(
                FIX_SUMMARIES_SYSTEM_PROMPT, user_message, model=self._secondary_model
            )
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
            content = self._call_claude(
                ENTITY_MATCH_SYSTEM_PROMPT, user_message, model=self._secondary_model
            )
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
