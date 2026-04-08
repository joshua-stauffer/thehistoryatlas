#!/usr/bin/env python
"""
Classify existing summaries into themes using the Anthropic Batch API.

Reads all summaries that don't yet have theme assignments, submits them
to Claude (Haiku by default) via the Batch API (50% discount), and writes
the results back to the summary_themes table.

Usage:
    python backfill_themes.py                    # Run full backfill
    python backfill_themes.py --model sonnet     # Use a different model
    python backfill_themes.py --dry-run          # Show what would be submitted
    python backfill_themes.py --resume BATCH_ID  # Resume polling a submitted batch
    python backfill_themes.py --limit 100        # Only process first N untagged summaries
"""

import argparse
import json
import logging
import os
import sys
import time
from uuid import uuid4

import anthropic
import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
}

# All subcategory slugs — the only valid classification targets.
VALID_SLUGS = [
    # Arts & Culture
    "music",
    "visual-arts",
    "literature",
    "theater-and-film",
    "architecture",
    "fashion-and-design",
    # Science & Technology
    "astronomy-and-space",
    "natural-science",
    "medicine",
    "invention-and-engineering",
    "mathematics",
    "exploration-and-navigation",
    # Politics & Power
    "war-and-conflict",
    "diplomacy",
    "governance",
    "revolution",
    "royalty-and-dynasty",
    "espionage-and-intelligence",
    # Society
    "religion",
    "education",
    "philosophy-and-ideas",
    "social-movement",
    "economics-and-trade",
    "crime-and-justice",
    # Daily Life
    "food-and-cuisine",
    "sports-and-athletics",
    "love-and-relationships",
    "migration",
    "customs-and-traditions",
]

CLASSIFICATION_SYSTEM_PROMPT = f"""You classify historical event summaries into 1-3 thematic tags.

Available tags (use only these exact slugs):
{json.dumps(VALID_SLUGS)}

Rules:
- Assign 1-3 tags per event. Most events need just 1-2.
- The first tag is the primary (most relevant) theme.
- Tags can cross categories (e.g. an invention related to music gets both "invention-and-engineering" and "music").
- Only use tags that clearly apply. When in doubt, fewer is better.

Return ONLY a JSON array of objects, one per event, in the same order as the input. Each object has:
- "id": the event ID (string, passed through from input)
- "themes": array of slug strings, primary first
- "confidence": float 0.0-1.0 for the primary theme

Example response:
[
  {{"id": "abc-123", "themes": ["war-and-conflict", "diplomacy"], "confidence": 0.95}},
  {{"id": "def-456", "themes": ["literature"], "confidence": 0.88}}
]"""

# How many summaries per batch request message (keeps token count manageable)
EVENTS_PER_REQUEST = 20
# Anthropic batch API max requests
MAX_BATCH_REQUESTS = 10000


def get_db_connection():
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        log.error("THA_DB_URI environment variable is required")
        sys.exit(1)
    return psycopg2.connect(db_uri)


def fetch_untagged_summaries(conn, limit=None):
    """Fetch summaries that have no entries in summary_themes."""
    query = """
        SELECT s.id, s.text
        FROM summaries s
        LEFT JOIN summary_themes st ON s.id = st.summary_id
        WHERE st.id IS NULL
        ORDER BY s.id
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()


def fetch_slug_to_id(conn):
    """Load the theme slug→UUID mapping from the DB."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, slug FROM themes WHERE parent_id IS NOT NULL")
        rows = cur.fetchall()
    return {row["slug"]: row["id"] for row in rows}


def build_batch_requests(summaries, model):
    """Group summaries into batch request payloads."""
    requests = []
    for batch_start in range(0, len(summaries), EVENTS_PER_REQUEST):
        batch = summaries[batch_start : batch_start + EVENTS_PER_REQUEST]
        events_text = "\n".join(
            f'- ID: {row["id"]}\n  Text: {row["text"]}' for row in batch
        )
        user_message = f"Classify these historical events:\n\n{events_text}"
        requests.append(
            {
                "custom_id": f"themes-{batch_start:06d}",
                "params": {
                    "model": model,
                    "max_tokens": 4096,
                    "system": [
                        {
                            "type": "text",
                            "text": CLASSIFICATION_SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    "messages": [{"role": "user", "content": user_message}],
                },
            }
        )
    return requests


def submit_batch(client, requests):
    """Submit a batch and return the batch ID."""
    batch = client.messages.batches.create(requests=requests)
    log.info(f"Submitted batch {batch.id} with {len(requests)} requests")
    return batch.id


def poll_batch(client, batch_id, poll_interval=30):
    """Poll until batch completes, then return results."""
    while True:
        status = client.messages.batches.retrieve(batch_id)
        counts = status.request_counts
        log.info(
            f"Batch {batch_id}: {status.processing_status} — "
            f"{counts.processing} processing, {counts.succeeded} succeeded, "
            f"{counts.errored} errored"
        )
        if status.processing_status == "ended":
            break
        time.sleep(poll_interval)

    results = []
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text.strip()
            try:
                parsed = json.loads(text)
                results.extend(parsed)
            except json.JSONDecodeError:
                log.error(f"Failed to parse JSON from {result.custom_id}: {text[:200]}")
        else:
            log.error(
                f"Request {result.custom_id} failed: {result.result.type}"
            )
    return results


def write_results(conn, results, slug_to_id):
    """Write classification results to summary_themes."""
    inserted = 0
    skipped = 0
    with conn.cursor() as cur:
        for item in results:
            summary_id = item.get("id")
            themes = item.get("themes", [])
            confidence = item.get("confidence")

            if not summary_id or not themes:
                skipped += 1
                continue

            for i, slug in enumerate(themes[:3]):  # max 3 themes
                theme_id = slug_to_id.get(slug)
                if not theme_id:
                    log.warning(f"Unknown slug '{slug}' for summary {summary_id}")
                    skipped += 1
                    continue
                try:
                    cur.execute(
                        """
                        INSERT INTO summary_themes (id, summary_id, theme_id, is_primary, confidence)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (summary_id, theme_id) DO NOTHING
                        """,
                        (
                            str(uuid4()),
                            summary_id,
                            str(theme_id),
                            i == 0,  # first theme is primary
                            confidence if i == 0 else None,
                        ),
                    )
                    inserted += 1
                except Exception as e:
                    log.error(f"Failed to insert theme for {summary_id}: {e}")
                    conn.rollback()
                    skipped += 1

    conn.commit()
    log.info(f"Inserted {inserted} theme associations, skipped {skipped}")


def main():
    parser = argparse.ArgumentParser(description="Backfill theme tags for summaries")
    parser.add_argument(
        "--model",
        choices=list(MODEL_MAP.keys()),
        default="haiku",
        help="Model to use (default: haiku)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be submitted without calling the API",
    )
    parser.add_argument(
        "--resume",
        metavar="BATCH_ID",
        help="Resume polling an already-submitted batch",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process first N untagged summaries",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between batch status checks (default: 30)",
    )
    args = parser.parse_args()

    conn = get_db_connection()
    slug_to_id = fetch_slug_to_id(conn)
    log.info(f"Loaded {len(slug_to_id)} theme slugs from DB")

    if not slug_to_id:
        log.error("No themes found in DB. Run migrations first.")
        sys.exit(1)

    model = MODEL_MAP[args.model]
    client = anthropic.Anthropic()

    if args.resume:
        log.info(f"Resuming batch {args.resume}")
        results = poll_batch(client, args.resume, poll_interval=args.poll_interval)
        write_results(conn, results, slug_to_id)
        conn.close()
        return

    summaries = fetch_untagged_summaries(conn, limit=args.limit)
    log.info(f"Found {len(summaries)} untagged summaries")

    if not summaries:
        log.info("Nothing to do.")
        conn.close()
        return

    requests = build_batch_requests(summaries, model)
    log.info(
        f"Built {len(requests)} batch requests "
        f"({len(summaries)} summaries, {EVENTS_PER_REQUEST} per request)"
    )

    if args.dry_run:
        log.info("Dry run — not submitting. First request preview:")
        print(json.dumps(requests[0], indent=2, default=str))
        conn.close()
        return

    if len(requests) > MAX_BATCH_REQUESTS:
        log.error(
            f"Too many requests ({len(requests)}) for a single batch "
            f"(max {MAX_BATCH_REQUESTS}). Use --limit to process in chunks."
        )
        sys.exit(1)

    batch_id = submit_batch(client, requests)
    log.info(f"Batch ID: {batch_id} — use --resume {batch_id} if interrupted")
    results = poll_batch(client, batch_id, poll_interval=args.poll_interval)
    write_results(conn, results, slug_to_id)
    conn.close()
    log.info("Done.")


if __name__ == "__main__":
    main()
