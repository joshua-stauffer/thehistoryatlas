"""Targeted test for time-precision extraction.

Runs the extraction prompt against time_precision_test.pdf and checks
that each extracted event's time precision matches the expectations in
time_precision_cases.json.

Does NOT require a running server — only CLAUDE_API_KEY.

Usage:
    cd text_reader
    CLAUDE_API_KEY=sk-ant-... python experiments/test_time_precision.py
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent))
from text_reader.claude_client import EXTRACTION_SYSTEM_PROMPT

HERE = Path(__file__).parent.parent
CASES_FILE = HERE / "sources" / "time_precision_cases.json"
PDF_FILE = HERE / "sources" / "time_precision_test.pdf"


def extract_pdf_text(path: Path) -> str:
    doc = fitz.open(str(path))
    return "\n".join(page.get_text() for page in doc)


def run_extraction(text: str, api_key: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key)
    user_msg = (
        "Source: Time Precision Test\n"
        "Author: Test\n\n"
        f"<source_text>\n{text}\n</source_text>"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    content = response.content[0].text.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(content)


def find_event(
    events: list[dict], summary_contains: str, also_contains: str | None
) -> dict | None:
    """Return the first event whose summary contains both match strings."""
    for e in events:
        s = e.get("summary", "").lower()
        if summary_contains.lower() in s:
            if also_contains is None or also_contains.lower() in s:
                return e
    return None


def run_checks(events: list[dict], cases: list[dict]) -> tuple[int, int]:
    passed = failed = 0

    for case in cases:
        case_id = case["id"]
        for check in case["checks"]:
            match_key = check["summary_contains"]
            also_key = check.get("also_contains")
            expected = check["expected_precision"]
            note = check["note"]

            event = find_event(events, match_key, also_key)
            if event is None:
                search = f"{match_key!r}"
                if also_key:
                    search += f" + {also_key!r}"
                print(f"  [MISS ] [{case_id}] No event matched {search}")
                print(f"          {note}")
                failed += 1
                continue

            actual = event["time"]["precision"]
            time_name = event["time"]["name"]
            time_date = event["time"]["date"]
            ok = actual == expected

            status = "PASS " if ok else "FAIL "
            precision_label = {
                7: "century",
                8: "decade",
                9: "year",
                10: "month",
                11: "day",
            }.get(actual, str(actual))
            expected_label = {
                7: "century",
                8: "decade",
                9: "year",
                10: "month",
                11: "day",
            }.get(expected, str(expected))

            detail = f"precision={actual} ({precision_label})"
            if not ok:
                detail += f" — expected {expected} ({expected_label})"
            detail += f", name={time_name!r}, date={time_date}"

            print(f"  [{status}] [{case_id}] {detail}")
            print(f"          {note}")
            if ok:
                passed += 1
            else:
                failed += 1

    return passed, failed


def main():
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("ERROR: CLAUDE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not CASES_FILE.exists():
        print(f"ERROR: {CASES_FILE} not found")
        sys.exit(1)
    if not PDF_FILE.exists():
        print(
            f"ERROR: {PDF_FILE} not found — run sources/make_time_precision_test.py first"
        )
        sys.exit(1)

    data = json.loads(CASES_FILE.read_text())
    cases = data["cases"]
    total_checks = sum(len(c["checks"]) for c in cases)

    print(
        f"Cases file: {CASES_FILE.name} ({len(cases)} entries, {total_checks} checks)"
    )
    print(f"PDF file:   {PDF_FILE.name}")

    text = extract_pdf_text(PDF_FILE)
    print(f"PDF text:   {len(text)} chars\n")

    print("Running extraction (synchronous, claude-sonnet-4-6)...")
    t0 = time.time()
    events = run_extraction(text, api_key)
    elapsed = time.time() - t0
    print(f"  {len(events)} events extracted in {elapsed:.1f}s\n")

    print("=== All extracted time fields ===")
    for e in events:
        t = e.get("time", {})
        p = t.get("precision")
        label = {7: "century", 8: "decade", 9: "year", 10: "month", 11: "day"}.get(
            p, str(p)
        )
        print(
            f"  [{p:2d} {label:7s}] {t.get('name')!r:28s} {t.get('date')}"
            f"  | {e.get('summary', '')[:55]}"
        )

    print("\n=== Precision checks ===")
    passed, failed = run_checks(events, cases)

    print(f"\nResult: {passed}/{passed + failed} checks passed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
