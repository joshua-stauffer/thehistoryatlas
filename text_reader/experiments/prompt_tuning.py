"""Prompt-tuning experiment for extraction quality.

Runs the extraction prompt multiple times on the same text chunk via the
Message Batches API, then reports validation statistics.

Usage:
    python experiments/prompt_tuning.py [--runs N] [--prompt-file FILE]
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import anthropic
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Add parent dir to path so we can import text_reader
sys.path.insert(0, str(Path(__file__).parent.parent))
from text_reader.claude_client import EXTRACTION_SYSTEM_PROMPT
from text_reader.types import (
    ExtractedEvent,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedTime,
)


# ---- Configuration ----

PDF_PATH = str(
    Path(__file__).parent.parent
    / "sources"
    / "Grove's_dictionary_of_music_and_musicians_3.pdf"
)
START_PAGE = 168
END_PAGE = 172
MODEL = "claude-haiku-4-5-20251001"
SOURCE_TITLE = "Grove's Dictionary of Music and Musicians, 2nd Edition"
SOURCE_AUTHOR = "Sir George Grove"


# ---- Helpers ----


def extract_text(pdf_path: str, start: int, end: int) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for i in range(start - 1, end):
        text += doc[i].get_text()
    doc.close()
    return text


def validate_event(event: ExtractedEvent) -> list[str]:
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


def parse_response(content: str) -> list[ExtractedEvent]:
    """Parse a raw JSON response into ExtractedEvents (best-effort)."""
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
        log.error(f"JSON parse failed: {content[:200]}")
        return []

    events = []
    for raw in raw_events:
        place_data = raw.get("place")
        time_data = raw.get("time")
        if not place_data or not time_data:
            continue
        try:
            events.append(
                ExtractedEvent(
                    summary=raw["summary"],
                    excerpt=raw.get("excerpt", ""),
                    people=[ExtractedPerson(**p) for p in raw.get("people", [])],
                    place=ExtractedPlace(**place_data),
                    time=ExtractedTime(**time_data),
                    confidence=raw.get("confidence", 0.5),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return events


def run_experiment(
    api_key: str,
    system_prompt: str,
    chunk_text: str,
    n_runs: int,
    label: str = "baseline",
    model: str = MODEL,
):
    """Submit n_runs identical extraction requests as a batch, then analyze results."""
    client = anthropic.Anthropic(api_key=api_key)

    user_message = (
        f"Extract historical events from this passage of "
        f'"{SOURCE_TITLE}" by {SOURCE_AUTHOR}:\n\n{chunk_text}'
    )

    # Estimate cost
    # Rough: ~8K tokens input, ~12K tokens output per run
    input_tokens_est = 8_000 * n_runs
    output_tokens_est = 12_000 * n_runs
    cost_est = (input_tokens_est * 0.40 / 1_000_000) + (
        output_tokens_est * 2.00 / 1_000_000
    )
    log.info(f"Estimated cost for {n_runs} runs: ${cost_est:.2f} (batch pricing)")

    # Build batch requests
    requests = []
    for i in range(n_runs):
        requests.append(
            {
                "custom_id": f"{label}-run-{i:03d}",
                "params": {
                    "model": model,
                    "max_tokens": 32768,
                    "system": [
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    "messages": [{"role": "user", "content": user_message}],
                },
            }
        )

    # Submit
    batch = client.messages.batches.create(requests=requests)
    log.info(f"Submitted batch {batch.id} with {n_runs} requests")

    # Poll
    while True:
        status = client.messages.batches.retrieve(batch.id)
        counts = status.request_counts
        log.info(
            f"Batch {batch.id}: {status.processing_status} — "
            f"{counts.processing} processing, {counts.succeeded} succeeded"
        )
        if status.processing_status == "ended":
            break
        time.sleep(15)

    # Collect results
    results = list(client.messages.batches.results(batch.id))
    results.sort(key=lambda r: r.custom_id)

    # Analyze
    all_run_stats = []
    total_input_tokens = 0
    total_output_tokens = 0

    for result in results:
        run_id = result.custom_id
        if result.result.type != "succeeded":
            log.warning(f"{run_id}: FAILED")
            continue

        msg = result.result.message
        total_input_tokens += msg.usage.input_tokens
        total_output_tokens += msg.usage.output_tokens

        events = parse_response(msg.content[0].text.strip())
        valid = 0
        invalid = 0
        missing_categories: dict[str, int] = {}
        event_details: list[dict] = []

        for event in events:
            missing = validate_event(event)
            detail = {
                "summary": event.summary,
                "people": [p.model_dump() for p in event.people],
                "place": event.place.model_dump(),
                "time": event.time.model_dump(),
                "excerpt": event.excerpt,
                "confidence": event.confidence,
                "valid": len(missing) == 0,
                "missing": missing,
            }
            event_details.append(detail)

            if missing:
                invalid += 1
                for m in missing:
                    is_person = any(m == p.name for p in event.people)
                    is_place = m == event.place.name
                    is_time = m == event.time.name
                    if is_person:
                        cat = "person"
                    elif is_place:
                        cat = "place"
                    elif is_time:
                        cat = "time"
                    else:
                        cat = "unknown"
                    missing_categories[cat] = missing_categories.get(cat, 0) + 1
            else:
                valid += 1

        total = valid + invalid
        pct = (valid / total * 100) if total else 0
        all_run_stats.append(
            {
                "run_id": run_id,
                "total": total,
                "valid": valid,
                "invalid": invalid,
                "valid_pct": pct,
                "missing_categories": missing_categories,
                "events": event_details,
            }
        )

    # Compute actual cost
    actual_cost = (total_input_tokens * 0.40 / 1_000_000) + (
        total_output_tokens * 2.00 / 1_000_000
    )

    # Print report
    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {label}")
    print(f"{'='*70}")
    print(f"Model: {model}")
    print(f"Runs: {n_runs}")
    print(f"Pages: {START_PAGE}-{END_PAGE}")
    print(f"Tokens: {total_input_tokens:,} input, {total_output_tokens:,} output")
    print(f"Cost: ${actual_cost:.3f}")
    print()

    # Per-run summary
    print(f"{'Run':<20} {'Total':>6} {'Valid':>6} {'Invalid':>8} {'Valid%':>7}")
    print("-" * 50)
    for s in all_run_stats:
        print(
            f"{s['run_id']:<20} {s['total']:>6} {s['valid']:>6} "
            f"{s['invalid']:>8} {s['valid_pct']:>6.1f}%"
        )

    # Aggregate stats
    if all_run_stats:
        avg_total = sum(s["total"] for s in all_run_stats) / len(all_run_stats)
        avg_valid = sum(s["valid"] for s in all_run_stats) / len(all_run_stats)
        avg_invalid = sum(s["invalid"] for s in all_run_stats) / len(all_run_stats)
        avg_pct = sum(s["valid_pct"] for s in all_run_stats) / len(all_run_stats)
        print("-" * 50)
        print(
            f"{'AVERAGE':<20} {avg_total:>6.1f} {avg_valid:>6.1f} "
            f"{avg_invalid:>8.1f} {avg_pct:>6.1f}%"
        )

        # Aggregate missing categories
        agg_missing: dict[str, int] = {}
        for s in all_run_stats:
            for cat, count in s["missing_categories"].items():
                agg_missing[cat] = agg_missing.get(cat, 0) + count
        if agg_missing:
            print(f"\nMissing entity breakdown (across all runs):")
            for cat in sorted(agg_missing, key=agg_missing.get, reverse=True):
                print(f"  {cat}: {agg_missing[cat]}")

    print(f"\n{'='*70}\n")

    return {
        "label": label,
        "runs": all_run_stats,
        "cost": actual_cost,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }


def main():
    parser = argparse.ArgumentParser(description="Prompt tuning experiment")
    parser.add_argument(
        "--runs", type=int, default=5, help="Number of runs per prompt variant"
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to a file containing the system prompt. Uses the default if not provided.",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="baseline",
        help="Label for this experiment run",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=START_PAGE,
        help="Start page to extract",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=END_PAGE,
        help="End page to extract",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL,
        help="Claude model ID to use",
    )
    args = parser.parse_args()

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        # Try loading from .env.local
        env_path = Path(__file__).parent.parent.parent / ".env.local"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("export "):
                    line = line[len("export ") :]
                if line.startswith("CLAUDE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        print("Error: CLAUDE_API_KEY not found in environment or .env.local")
        sys.exit(1)

    # Load prompt
    if args.prompt_file:
        system_prompt = Path(args.prompt_file).read_text()
        log.info(f"Loaded prompt from {args.prompt_file}")
    else:
        system_prompt = EXTRACTION_SYSTEM_PROMPT
        log.info("Using default EXTRACTION_SYSTEM_PROMPT")

    # Extract text
    chunk_text = extract_text(PDF_PATH, args.start_page, args.end_page)
    log.info(
        f"Extracted {len(chunk_text)} chars from pages {args.start_page}-{args.end_page}"
    )

    # Run experiment
    result = run_experiment(
        api_key=api_key,
        system_prompt=system_prompt,
        chunk_text=chunk_text,
        n_runs=args.runs,
        label=args.label,
        model=args.model,
    )

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    result_path = results_dir / f"{args.label}.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    log.info(f"Results saved to {result_path}")


if __name__ == "__main__":
    main()
