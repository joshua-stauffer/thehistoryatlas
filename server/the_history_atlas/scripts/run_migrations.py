#!/usr/bin/env python
"""
Script to run Alembic migrations.

This script runs Alembic migrations to apply database schema changes.

Usage:
    python run_migrations.py
"""

import logging
import os
import subprocess
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run Alembic migrations."""
    logger.info("Starting database migrations")

    # Get database connection string from environment variable
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        logger.error("THA_DB_URI environment variable is not set")
        sys.exit(1)

    # Change to the server directory where alembic.ini is located
    server_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    os.chdir(server_dir)

    try:
        # Run the migrations
        logger.info("Running database migrations with Alembic")
        result = subprocess.run(
            ["alembic", "upgrade", "head"], check=True, capture_output=True, text=True
        )
        logger.info(f"Migration output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Migration warnings: {result.stderr}")

        logger.info("Database migrations completed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
