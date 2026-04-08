#!/usr/bin/env python3

import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def update_database():
    """Add the last_books_search_offset column to the config table."""
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        log.error("THA_DB_URI environment variable not set")
        return 1

    engine = create_engine(db_uri)

    with engine.connect() as conn:
        log.info("Adding last_books_search_offset column if it doesn't exist")
        conn.execute(
            text(
                "ALTER TABLE config ADD COLUMN IF NOT EXISTS last_books_search_offset INTEGER DEFAULT 0;"
            )
        )
        conn.commit()

    log.info("Database update completed successfully")
    return 0


if __name__ == "__main__":
    exit(update_database())
