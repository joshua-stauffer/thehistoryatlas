#!/usr/bin/env python
"""
Monitor the process of calculating story orders by tracking tag_instances with null story_order values.
Prints progress, processing rates, and ETA to completion every minute.

Usage:
    python monitor_calculate_story_orders.py

Environment:
    THA_DB_URI: The database URI for The History Atlas database.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Get DB URI from environment
DB_URI = os.environ.get("THA_DB_URI")
if not DB_URI:
    print("Error: THA_DB_URI environment variable not set.")
    sys.exit(1)

engine = create_engine(DB_URI, future=True)

# In-memory state
history = []  # List of (timestamp, null_story_order_count, processed_count)

print("Starting story order calculation monitor...")
print(f"Connected to DB: {DB_URI}")
print("Press Ctrl+C to stop.\n")

try:
    # Get initial total count to track progress
    with engine.connect() as conn:
        total_records = conn.execute(
            text("SELECT COUNT(*) FROM tag_instances")
        ).scalar()

    while True:
        now = datetime.now()
        with engine.connect() as conn:
            null_story_order_count = conn.execute(
                text("SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL")
            ).scalar()
            processed_count = total_records - null_story_order_count

        # Add to history
        history.append((now, null_story_order_count, processed_count))
        # Keep only last 120 minutes (arbitrary, for memory)
        if len(history) > 120:
            history = history[-120:]

        # Calculate processing rate and ETA
        if len(history) > 1:
            prev_time, prev_null, prev_processed = history[-2]
            dt = (now - prev_time).total_seconds() / 60.0  # minutes
            dp = processed_count - prev_processed
            rate = dp / dt if dt > 0 else 0

            # Estimate time to finish
            eta_minutes = null_story_order_count / rate if rate > 0 else float("inf")
            eta_time = now + timedelta(minutes=eta_minutes) if rate > 0 else None

            completion_percent = (
                (processed_count / total_records) * 100 if total_records > 0 else 0
            )
        else:
            rate = eta_minutes = None
            eta_time = None
            completion_percent = (
                (processed_count / total_records) * 100 if total_records > 0 else 0
            )

        # Print status
        print(
            f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Remaining null story_order: {null_story_order_count}, Processed: {processed_count}/{total_records} ({completion_percent:.2f}%)"
        )
        if rate is not None:
            print(f"  Records processed/min: {rate:.2f}")
            if eta_time:
                print(
                    f"  ETA (all processed): {eta_time.strftime('%Y-%m-%d %H:%M:%S')} ({eta_minutes:.1f} min)"
                )
        print()
        time.sleep(60)
except KeyboardInterrupt:
    print("\nMonitor stopped.")
