#!/usr/bin/env python
"""
Monitor the WikiLink build process by tracking the number of rows in wiki_queue and created_events tables.
Prints progress, processing rates, and ETA to completion every minute.

Usage:
    python monitor_build.py

Environment:
    WIKILINK_DB_URI: The database URI for WikiLink's database.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Get DB URI from environment
DB_URI = os.environ.get("WIKILINK_DB_URI")
if not DB_URI:
    print("Error: WIKILINK_DB_URI environment variable not set.")
    sys.exit(1)

engine = create_engine(DB_URI, future=True)

# In-memory state
history = []  # List of (timestamp, wiki_queue_count, created_events_count)

print("Starting WikiLink build monitor...")
print(f"Connected to DB: {DB_URI}")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        now = datetime.now()
        with engine.connect() as conn:
            wiki_queue_count = conn.execute(
                text("SELECT COUNT(*) FROM wiki_queue")
            ).scalar()
            created_events_count = conn.execute(
                text("SELECT COUNT(*) FROM created_events")
            ).scalar()

        # Add to history
        history.append((now, wiki_queue_count, created_events_count))
        # Keep only last 120 minutes (arbitrary, for memory)
        if len(history) > 120:
            history = history[-120:]

        # Calculate processing rate and ETA
        if len(history) > 1:
            prev_time, prev_queue, prev_events = history[-2]
            dt = (now - prev_time).total_seconds() / 60.0  # minutes
            dq = prev_queue - wiki_queue_count
            de = created_events_count - prev_events
            rate = dq / dt if dt > 0 else 0
            event_rate = de / dt if dt > 0 else 0
            avg_events_per_row = de / dq if dq > 0 else 0
            # Estimate time to finish
            eta_minutes = wiki_queue_count / rate if rate > 0 else float("inf")
            eta_time = now + timedelta(minutes=eta_minutes) if rate > 0 else None
            # Estimate total events
            expected_total_events = (
                created_events_count + (wiki_queue_count * avg_events_per_row)
                if avg_events_per_row > 0
                else None
            )
        else:
            rate = event_rate = avg_events_per_row = eta_minutes = None
            eta_time = expected_total_events = None

        # Print status
        print(
            f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] wiki_queue: {wiki_queue_count}, created_events: {created_events_count}"
        )
        if rate is not None:
            print(f"  Rows processed/min: {rate:.2f}")
            print(f"  Events created/min: {event_rate:.2f}")
            print(f"  Events per wiki_queue row: {avg_events_per_row:.2f}")
            if eta_time:
                print(
                    f"  ETA (rows=0): {eta_time.strftime('%Y-%m-%d %H:%M:%S')} ({eta_minutes:.1f} min)"
                )
            if expected_total_events:
                print(f"  Expected total events: {expected_total_events:.0f}")
        print()
        time.sleep(60)
except KeyboardInterrupt:
    print("\nMonitor stopped.")
