#!/usr/bin/env python
"""
Bulk calculate story orders for tag instances with null story_order values.

This is an optimized version of calculate_story_orders.py for handling large numbers
of null story_order values more efficiently.
"""

import argparse
import time
import os
import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Database connection string from environment
DB_URI = os.environ.get("THA_DB_URI")


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

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all story_order values to NULL before processing",
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


def reset_story_orders(session: Session):
    """Reset all story_order values to NULL."""
    print("Resetting all story_order values to NULL...")
    count = session.execute(
        text("UPDATE tag_instances SET story_order = NULL")
    ).rowcount
    session.commit()
    print(f"Reset {count} story_order values.")


def process_batch(
    session: Session, batch_size: int
) -> int:
    """
    Process a batch of tag instances with null story_order values.

    Instead of processing by tag_id (which can be slow when a single tag has millions of instances),
    this processes tag_instances directly in batches, respecting the 'after' relationships.

    Args:
        session: The database session
        batch_size: Number of tag instances to process in each batch
        include_timeless: Whether to include tag instances without time information

    Returns:
        The number of rows processed.
    """
    try:
        # Base query for instances with time information
        base_query = """
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
                    AND ti.after IS NOT NULL 
                    AND ti2.summary_id::text IN (
                        SELECT jsonb_array_elements_text(ti.after)
                    )
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

        update_count = session.execute(
            text(base_query),
            {"batch_size": batch_size},
        )

        # Commit the changes
        session.commit()

        # Return the number of rows affected
        return update_count.rowcount

    except Exception as e:
        # Roll back on error
        session.rollback()
        print(f"Error processing batch: {e}")
        raise


def log_progress(session, start_time, total_processed, batch_count):
    """Log progress of the processing."""
    elapsed = time.time() - start_time
    remaining = session.execute(
        text("SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL")
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
        eta_str = datetime.fromtimestamp(eta).strftime("%Y-%m-%d %H:%M:%S")
        print(f"ETA: {eta_str} ({eta_seconds/60:.1f} min)")

    print()


def main():
    if not DB_URI:
        print("Error: THA_DB_URI environment variable not set.")
        print(
            "Set it with: export THA_DB_URI=postgresql://user:password@host:port/dbname"
        )
        return 1

    args = parse_args()
    start_time = time.time()
    total_processed = 0
    batch_count = 0

    # Create engine and session factory directly
    engine = create_engine(DB_URI)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Reset story orders if requested
        if args.reset:
            reset_story_orders(session)

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
            if args.include_timeless:
                print("Including tag instances without time information")

            # First process instances with time information
            print("Processing tag instances with time information...")
            process_with_time = True

            while process_with_time:
                # Process a batch
                rows_processed = process_batch(
                    session, args.batch_size
                )
                total_processed += rows_processed
                batch_count += 1

                # If no rows were processed, we're either done or need to switch to timeless
                if rows_processed == 0:
                    if args.include_timeless:
                        process_with_time = False
                        print(
                            "\nSwitching to process tag instances without time information..."
                        )
                    else:
                        break  # Done completely

                # Log progress at specified intervals
                if batch_count % args.log_interval == 0:
                    log_progress(session, start_time, total_processed, batch_count)

            # Then process instances without time information if requested
            if args.include_timeless and not process_with_time:
                timeless_batch_count = 0

                while True:
                    # Process a batch of timeless instances
                    rows_processed = process_batch(
                        session, args.batch_size
                    )
                    total_processed += rows_processed
                    batch_count += 1
                    timeless_batch_count += 1

                    # If no rows were processed, we're done
                    if rows_processed == 0:
                        break

                    # Log progress at specified intervals
                    if timeless_batch_count % args.log_interval == 0:
                        log_progress(session, start_time, total_processed, batch_count)

                print(
                    f"\nProcessed timeless instances in {timeless_batch_count} batches"
                )

        finally:
            # Clean up temporary indexes if we created them
            if args.create_index:
                drop_indexes(session)

    total_time = time.time() - start_time
    print(
        f"Completed processing {total_processed:,} tag instances in {total_time:.1f} seconds"
    )
    print(f"Average processing rate: {total_processed/total_time:.1f} rows/sec")
    return 0


if __name__ == "__main__":
    exit(main())
