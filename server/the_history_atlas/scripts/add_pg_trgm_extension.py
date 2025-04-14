#!/usr/bin/env python3
import os
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """
    Migration script to add PostgreSQL trigram extension and create the necessary
    text search index on names table for fuzzy search functionality.
    """
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        raise ValueError("THA_DB_URI environment variable is not set")

    logger.info("Connecting to database")
    engine = create_engine(db_uri)

    with engine.connect() as conn:
        # Create a transaction to execute all statements
        with conn.begin():
            logger.info("Creating pg_trgm extension if it doesn't exist")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

            logger.info("Creating GIN index on names table for trigram-based search")
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_names_trgm_gin 
                ON names USING GIN (name gin_trgm_ops);
            """
                )
            )

            logger.info("Migration completed successfully")


if __name__ == "__main__":
    run_migration()
