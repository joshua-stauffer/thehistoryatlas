#!/usr/bin/env python
"""
Database initialization script

This script runs Alembic migrations to set up or update the database schema.
Use this script in production to manually run migrations.
"""

import os
import subprocess
import sys


def main():
    """Run Alembic migrations to initialize or update the database."""
    # Ensure we have a database URI
    db_uri = os.environ.get("THA_DB_URI")
    if not db_uri:
        print("Error: THA_DB_URI environment variable not set")
        sys.exit(1)

    # Run the migrations
    try:
        subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)
        print("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
