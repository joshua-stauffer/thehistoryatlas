#!/usr/bin/env python3
"""Backfill summary embeddings using OpenAI's text-embedding-3-small model.

Usage:
    python scripts/backfill_embeddings.py --db-uri "$THA_DB_URI"
    python scripts/backfill_embeddings.py --db-uri "$THA_DB_URI" --limit 100 --dry-run
    python scripts/backfill_embeddings.py --db-uri "$THA_DB_URI" --batch-size 100
"""

import argparse
import logging
import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

# text-embedding-3-small: 1536 dims, $0.02 / 1M tokens
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


def get_unembedded_summaries(engine, limit: int | None = None) -> list[tuple]:
    """Return (id, text) pairs for summaries without embeddings."""
    query = """
        select id, text from summaries
        where embedding is null and text is not null
        order by id
    """
    if limit:
        query += f" limit {limit}"
    with Session(engine, future=True) as session:
        return session.execute(text(query)).all()


def embed_batch(client, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenAI API."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def store_embeddings(
    engine, pairs: list[tuple], embeddings: list[list[float]]
) -> int:
    """Store embeddings in the database. Returns count stored."""
    stored = 0
    with Session(engine, future=True) as session:
        for (summary_id, _), embedding in zip(pairs, embeddings):
            session.execute(
                text("update summaries set embedding = :emb where id = :sid"),
                {"sid": summary_id, "emb": str(embedding)},
            )
            stored += 1
        session.commit()
    return stored


def main():
    parser = argparse.ArgumentParser(description="Backfill summary embeddings")
    parser.add_argument("--db-uri", required=True, help="PostgreSQL connection string")
    parser.add_argument("--api-key", default=None, help="OpenAI API key (or OPENAI_API_KEY env)")
    parser.add_argument("--batch-size", type=int, default=200, help="Texts per API call")
    parser.add_argument("--limit", type=int, default=None, help="Max summaries to embed")
    parser.add_argument("--dry-run", action="store_true", help="Count without embedding")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    engine = create_engine(args.db_uri)
    summaries = get_unembedded_summaries(engine, limit=args.limit)
    log.info(f"Found {len(summaries)} summaries without embeddings")

    if args.dry_run or not summaries:
        return

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        log.error("Set OPENAI_API_KEY or pass --api-key")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        log.error("pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    total_stored = 0
    total_tokens = 0

    for i in range(0, len(summaries), args.batch_size):
        batch = summaries[i : i + args.batch_size]
        texts = [s[1] for s in batch]

        log.info(
            f"Embedding batch {i // args.batch_size + 1} "
            f"({len(batch)} texts, {i + len(batch)}/{len(summaries)} total)"
        )

        embeddings = embed_batch(client, texts)
        stored = store_embeddings(engine, batch, embeddings)
        total_stored += stored

        # Estimate tokens (~4 chars per token)
        total_tokens += sum(len(t) for t in texts) // 4

        if i + args.batch_size < len(summaries):
            time.sleep(0.5)  # rate limit courtesy

    cost = total_tokens * 0.02 / 1_000_000
    log.info(
        f"Done. Embedded {total_stored} summaries. "
        f"~{total_tokens:,} tokens, ~${cost:.4f}"
    )


if __name__ == "__main__":
    main()
