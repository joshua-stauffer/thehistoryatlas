"""Regression test for extraction quality.

Tests all behavioral categories tuned during development:
  - Collective references (e.g. 'the sisters Milanollo' → both named individually)
  - Full name in every summary (primary subject must use full name)
  - Place verbatim in summary (even when implied from context)
  - Date-range splitting ('1843-45' → two events)
  - Time precision (century/decade/year/month/day hierarchy)
  - Completeness (all events extracted from a biographical entry)
  - Organizations not people (author, not publisher, for publications)

Does NOT require a running server — only CLAUDE_API_KEY.

Usage:
    cd text_reader
    CLAUDE_API_KEY=sk-ant-... python experiments/test_extraction_regression.py

Compare against an older prompt:
    git show <commit>:text_reader/text_reader/claude_client.py \\
        | python3 -c "
import sys, re
content = sys.stdin.read()
m = re.search(r'EXTRACTION_SYSTEM_PROMPT = \"\"\"(.*?)\"\"\"', content, re.DOTALL)
print(m.group(1) if m else '')
" > /tmp/old_prompt.txt
    CLAUDE_API_KEY=sk-ant-... python experiments/test_extraction_regression.py --prompt /tmp/old_prompt.txt
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).parent.parent))
from text_reader.claude_client import EXTRACTION_SYSTEM_PROMPT

CASES_FILE = (
    Path(__file__).parent.parent / "sources" / "extraction_regression_cases.json"
)

PRECISION_LABELS = {7: "century", 8: "decade", 9: "year", 10: "month", 11: "day"}


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def run_extraction(text: str, system_prompt: str, api_key: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key)
    user_msg = (
        "Source: Regression Test\n"
        "Author: Test\n\n"
        f"<source_text>\n{text}\n</source_text>"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    content = response.content[0].text.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(content)


# ---------------------------------------------------------------------------
# Event matching
# ---------------------------------------------------------------------------


def find_event(
    events: list[dict], summary_contains: str, also_contains: str | None
) -> dict | None:
    for e in events:
        s = e.get("summary", "").lower()
        if summary_contains.lower() in s:
            if also_contains is None or also_contains.lower() in s:
                return e
    return None


# ---------------------------------------------------------------------------
# Check runners
# ---------------------------------------------------------------------------


def run_check(check: dict, events: list[dict]) -> tuple[bool, str]:
    """Return (passed, detail_message)."""
    summary_contains = check["summary_contains"]
    also_contains = check.get("also_contains")
    check_type = check["check_type"]
    note = check["note"]

    event = find_event(events, summary_contains, also_contains)

    if check_type == "event_exists":
        ok = event is not None
        search_desc = repr(summary_contains)
        if also_contains:
            search_desc += f" + {also_contains!r}"
        if ok:
            return True, f"event found matching {search_desc}"
        else:
            return False, f"no event matched {search_desc}"

    if event is None:
        search_desc = repr(summary_contains)
        if also_contains:
            search_desc += f" + {also_contains!r}"
        return False, f"no event matched {search_desc} — cannot check {check_type}"

    if check_type == "precision":
        expected = check["expected_precision"]
        actual = event["time"]["precision"]
        ok = actual == expected
        expected_label = PRECISION_LABELS.get(expected, str(expected))
        actual_label = PRECISION_LABELS.get(actual, str(actual))
        detail = f"precision={actual} ({actual_label})"
        if not ok:
            detail += f" — expected {expected} ({expected_label})"
        detail += f", time.name={event['time']['name']!r}"
        return ok, detail

    if check_type == "person_in_event":
        expected_frag = check["expected_person_contains"]
        people = event.get("people", [])
        match = next(
            (
                p
                for p in people
                if expected_frag.lower() in p.get("name", "").lower()
                or expected_frag.lower() in p.get("full_name", "").lower()
            ),
            None,
        )
        ok = match is not None
        if ok:
            return (
                True,
                f"found person {match['name']!r} (full_name={match.get('full_name')!r})",
            )
        else:
            names_found = [p.get("name", "") for p in people]
            return False, f"no person containing {expected_frag!r}; got {names_found}"

    if check_type == "name_in_summary":
        expected_sub = check["expected_substring"]
        ok = expected_sub in event["summary"]
        detail = f"summary={event['summary'][:80]!r}"
        if not ok:
            detail = f"missing {expected_sub!r}; " + detail
        return ok, detail

    if check_type == "time_name":
        expected_name = check["expected_time_name"]
        actual_name = event["time"]["name"]
        ok = actual_name == expected_name
        detail = f"time.name={actual_name!r}"
        if not ok:
            detail = f"expected {expected_name!r}, got {actual_name!r}"
        return ok, detail

    return False, f"unknown check_type {check_type!r}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Extraction regression test")
    parser.add_argument(
        "--prompt",
        metavar="FILE",
        help="Path to a plain-text file containing the system prompt (default: current EXTRACTION_SYSTEM_PROMPT)",
    )
    parser.add_argument(
        "--category",
        metavar="CAT",
        help="Only run cases whose category matches this string",
    )
    args = parser.parse_args()

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("ERROR: CLAUDE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not CASES_FILE.exists():
        print(f"ERROR: {CASES_FILE} not found")
        sys.exit(1)

    if args.prompt:
        prompt_path = Path(args.prompt)
        if not prompt_path.exists():
            print(f"ERROR: prompt file not found: {prompt_path}")
            sys.exit(1)
        system_prompt = prompt_path.read_text()
        prompt_label = f"custom ({prompt_path.name})"
    else:
        system_prompt = EXTRACTION_SYSTEM_PROMPT
        prompt_label = "current (claude_client.py)"

    data = json.loads(CASES_FILE.read_text())
    cases = data["cases"]

    if args.category:
        cases = [c for c in cases if c.get("category", "") == args.category]
        if not cases:
            print(f"No cases found for category {args.category!r}")
            sys.exit(1)

    total_checks = sum(len(c["checks"]) for c in cases)
    print(f"Prompt:       {prompt_label}")
    print(
        f"Cases file:   {CASES_FILE.name} ({len(cases)} cases, {total_checks} checks)"
    )
    print()

    passed_total = failed_total = 0

    for case in cases:
        case_id = case["id"]
        category = case.get("category", "")
        description = case.get("description", "")
        source_text = case["source_text"]
        checks = case["checks"]

        print(f"[{case_id}] {description}")
        print(f"  category: {category}")

        t0 = time.time()
        try:
            events = run_extraction(source_text, system_prompt, api_key)
        except Exception as exc:
            print(f"  ERROR extracting: {exc}")
            failed_total += len(checks)
            print()
            continue
        elapsed = time.time() - t0
        print(f"  {len(events)} event(s) extracted in {elapsed:.1f}s")

        passed = failed = 0
        for check in checks:
            ok, detail = run_check(check, events)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {check['note']}")
            print(f"         → {detail}")
            if ok:
                passed += 1
            else:
                failed += 1

        passed_total += passed
        failed_total += failed
        result_line = f"  {passed}/{passed + failed} checks passed"
        print(result_line)
        print()

    print("=" * 60)
    print(
        f"TOTAL: {passed_total}/{passed_total + failed_total} checks passed"
        f" ({failed_total} failed)"
    )
    sys.exit(0 if failed_total == 0 else 1)


if __name__ == "__main__":
    main()
