#!/usr/bin/env python3

import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def add_time_index():
    """Add an index on time_added column in wiki_queue table to improve performance."""
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        log.error("THA_DB_URI environment variable not set")
        return 1

    engine = create_engine(db_uri)

    with engine.connect() as conn:
        log.info("Checking if index already exists")
        index_exists = conn.execute(
            text(
                """
                SELECT 1 
                FROM pg_indexes 
                WHERE indexname = 'idx_wiki_queue_time_added'
                """
            )
        ).fetchone()

        if index_exists:
            log.info("Index already exists, no action required")
        else:
            log.info("Creating index on wiki_queue.time_added")
            conn.execute(
                text(
                    """
                    CREATE INDEX idx_wiki_queue_time_added 
                    ON wiki_queue(time_added)
                    """
                )
            )
            conn.commit()
            log.info("Index created successfully")

    log.info("Database update completed successfully")
    return 0


if __name__ == "__main__":
    exit(add_time_index())
