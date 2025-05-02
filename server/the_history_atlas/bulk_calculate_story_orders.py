#!/usr/bin/env python
"""
Bulk calculate story orders for tag instances with null story_order values.

This is an optimized version of calculate_story_orders.py for handling large numbers
of null story_order values more efficiently.
"""

import argparse
import time
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bulk calculate story order for tag instances with null story_order values."
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of tag instances to process in each batch",
    )

    parser.add_argument(
        "--log-interval",
        type=int,
        default=10,
        help="Log progress after processing this many batches",
    )

    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Create temporary indexes to speed up processing",
    )

    return parser.parse_args()


def create_indexes(session: Session):
    """Create temporary indexes to speed up queries."""
    print("Creating temporary indexes to optimize processing...")
    session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS temp_story_order_null_idx 
        ON tag_instances (tag_id) 
        WHERE story_order IS NULL
    """
        )
    )

    # Index on summaries for faster joins
    session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS temp_summary_id_idx 
        ON tag_instances (summary_id)
    """
        )
    )

    # Index on time tags for faster access
    session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS temp_tag_type_idx 
        ON tags (id, type) 
        WHERE type = 'TIME'
    """
        )
    )

    session.commit()
    print("Indexes created.")


def drop_indexes(session: Session):
    """Drop the temporary indexes."""
    print("Dropping temporary indexes...")
    session.execute(text("DROP INDEX IF EXISTS temp_story_order_null_idx"))
    session.execute(text("DROP INDEX IF EXISTS temp_summary_id_idx"))
    session.execute(text("DROP INDEX IF EXISTS temp_tag_type_idx"))
    session.commit()
    print("Indexes dropped.")


def process_batch(session: Session, batch_size: int) -> int:
    """
    Process a batch of tag instances with null story_order values.

    Instead of processing by tag_id (which can be slow when a single tag has millions of instances),
    this processes tag_instances directly in batches, respecting the 'after' relationships.

    Returns the number of rows processed.
    """
    # A more complex query that handles 'after' dependencies:
    # 1. Select a batch of tag instances with NULL story_order
    # 2. Join with time information
    # 3. For each tag instance, find the maximum story_order of any instances in its 'after' array
    # 4. Assign new story_order values based on date and 'after' constraints

    update_count = session.execute(
        text(
            """
        WITH batch AS (
            SELECT 
                ti.id,
                ti.tag_id,
                ti.after,
                MIN(times.datetime) as event_datetime,
                MIN(times.precision) as event_precision,
                (
                    SELECT MAX(ti2.story_order) 
                    FROM tag_instances ti2 
                    WHERE ti2.tag_id = ti.tag_id 
                    AND (ti.after IS NOT NULL AND ti2.summary_id = ANY(ti.after::uuid[]))
                ) as max_after_story_order
            FROM tag_instances ti
            JOIN summaries s ON s.id = ti.summary_id
            JOIN tag_instances time_ti ON time_ti.summary_id = s.id
            JOIN tags time_tags ON time_tags.id = time_ti.tag_id AND time_tags.type = 'TIME'
            JOIN times ON times.id = time_tags.id
            WHERE ti.story_order IS NULL
            GROUP BY ti.id, ti.tag_id, ti.after
            LIMIT :batch_size
        ),
        -- Calculate row numbers within each tag_id, respecting both datetime and 'after' constraints
        ordered_batch AS (
            SELECT
                id,
                tag_id,
                CASE
                    -- If there are 'after' constraints, use max_after_story_order + 1000 as base
                    WHEN max_after_story_order IS NOT NULL THEN
                        max_after_story_order + 1000 + (ROW_NUMBER() OVER (
                            PARTITION BY tag_id, (max_after_story_order IS NOT NULL)
                            ORDER BY event_datetime, event_precision
                        ) * 10)
                    -- Otherwise use the default base (100000) with spacing of 1000
                    ELSE
                        100000 + (ROW_NUMBER() OVER (
                            PARTITION BY tag_id, (max_after_story_order IS NULL)
                            ORDER BY event_datetime, event_precision
                        ) * 1000)
                END as new_story_order
            FROM batch
        )
        UPDATE tag_instances 
        SET story_order = ob.new_story_order
        FROM ordered_batch ob
        WHERE tag_instances.id = ob.id
        """
        ),
        {"batch_size": batch_size},
    )

    # Commit the changes
    session.commit()

    # Return the number of rows affected
    return update_count.rowcount


def main():
    args = parse_args()
    start_time = time.time()
    total_processed = 0
    batch_count = 0

    # Set up the app manager to get access to the database connection
    config_app = Config()
    app_manager = AppManager(config_app=config_app)

    # Get a direct session for better performance
    engine = app_manager.history_app._repository._engine

    with Session(engine) as session:
        # Create temporary indexes if requested
        if args.create_index:
            create_indexes(session)

        try:
            # Get initial count of NULL story_order values
            null_count = session.execute(
                text("SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL")
            ).scalar()

            print(
                f"Starting bulk story order calculation with {null_count:,} NULL values"
            )
            print(f"Using batch size of {args.batch_size}")

            while True:
                # Process a batch
                rows_processed = process_batch(session, args.batch_size)
                total_processed += rows_processed
                batch_count += 1

                # If no rows were processed, we're done
                if rows_processed == 0:
                    break

                # Log progress at specified intervals
                if batch_count % args.log_interval == 0:
                    elapsed = time.time() - start_time
                    remaining = session.execute(
                        text(
                            "SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL"
                        )
                    ).scalar()

                    rate = total_processed / elapsed if elapsed > 0 else 0
                    eta_seconds = remaining / rate if rate > 0 else float("inf")

                    print(
                        f"Processed {total_processed:,} rows in {batch_count} batches ({elapsed:.1f}s)"
                    )
                    print(f"Processing rate: {rate:.1f} rows/sec")
                    print(f"Remaining: {remaining:,} rows")

                    if eta_seconds < float("inf"):
                        eta = datetime.now().timestamp() + eta_seconds
                        eta_str = datetime.fromtimestamp(eta).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        print(f"ETA: {eta_str} ({eta_seconds/60:.1f} min)")

                    print()

        finally:
            # Clean up temporary indexes if we created them
            if args.create_index:
                drop_indexes(session)

    total_time = time.time() - start_time
    print(
        f"Completed processing {total_processed:,} tag instances in {total_time:.1f} seconds"
    )
    print(f"Average processing rate: {total_processed/total_time:.1f} rows/sec")


if __name__ == "__main__":
    main()
