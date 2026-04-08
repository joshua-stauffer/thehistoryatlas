#!/usr/bin/env python
"""
Update tag_instances.story_order for all rows where it's currently NULL.

Each tag_instances row will be assigned a story_order value that follows these rules:
- For a given tag_id, rows will be ordered first by datetime, then by precision
- The earliest row gets a story_order of 100000, with each subsequent row 1000 higher
- There's a unique constraint between story_order and tag_id

Usage:
    python update_story_order.py                # Fix ordering issues for all tags
    python update_story_order.py --update-all   # Update all NULL story_orders
    python update_story_order.py --update-all --workers N  # Update with N parallel workers
    python update_story_order.py --reset-all    # Reset all story_orders to NULL
    python update_story_order.py --verify       # Verify ordering for random sample of tags
    python update_story_order.py --tag TAG_ID   # Fix ordering for a specific tag
    python update_story_order.py --verify-tag TAG_ID  # Verify ordering for a specific tag
    python update_story_order.py --reset-tag TAG_ID   # Reset story_orders for a specific tag
"""
import os
import sys
from datetime import datetime
import multiprocessing
from multiprocessing import Pool
from functools import partial

import psycopg2
import psycopg2.extras
import time
import argparse
from collections import defaultdict
import uuid
import re

# Register UUID adapter for PostgreSQL
psycopg2.extras.register_uuid()

# Get DB URI from environment
DB_URI = os.environ.get("THA_DB_URI")
if not DB_URI:
    print("Error: THA_DB_URI environment variable not set.")
    sys.exit(1)


def parse_date_for_sorting(date_str):
    """
    Parse a datetime string and return a tuple suitable for chronological sorting.
    Handles both BCE dates (negative years) and CE dates (positive years).

    A date string like "+0079-06-24T00:00:00Z" becomes (79, 6, 24, 0, 0, 0)
    A date string like "-0578-00-00T00:00:00Z" becomes (-578, 0, 0, 0, 0, 0)

    The result is suitable for direct comparison in chronological order.
    """
    if not date_str:
        return (float("inf"),)  # Put None/empty dates at the end

    # Extract sign and numerical components
    match = re.match(
        r"([+-])(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z", date_str
    )

    if not match:
        # Handle partial dates like "+0079-00-00T00:00:00Z"
        match = re.match(r"([+-])(\d{4})-(\d{2})-(\d{2})T", date_str)
        if match:
            sign, year, month, day = match.groups()
            hour, minute, second = 0, 0, 0
        else:
            # Try even more simplified format "+0079-00-00"
            match = re.match(r"([+-])(\d{4})-(\d{2})-(\d{2})", date_str)
            if match:
                sign, year, month, day = match.groups()
                hour, minute, second = 0, 0, 0
            else:
                # Ultimate fallback for very partial dates like "+0079-00-00"
                match = re.match(r"([+-])(\d{4})-(\d{2})", date_str)
                if match:
                    sign, year, month = match.groups()
                    day, hour, minute, second = 0, 0, 0, 0
                else:
                    # Final fallback for just year "+0079"
                    match = re.match(r"([+-])(\d{4})", date_str)
                    if match:
                        sign, year = match.groups()
                        month, day, hour, minute, second = 0, 0, 0, 0, 0
                    else:
                        # If we can't parse it at all, return a tuple that sorts last
                        return (float("inf"),)
    else:
        sign, year, month, day, hour, minute, second = match.groups()

    # Convert strings to integers, handling "00" values
    year = int(year)
    month = int(month) if month != "00" else 0
    day = int(day) if day != "00" else 0
    hour = int(hour) if "hour" in locals() else 0
    minute = int(minute) if "minute" in locals() else 0
    second = int(second) if "second" in locals() else 0

    # Apply sign to year for BCE dates
    if sign == "-":
        year = -year

    return (year, month, day, hour, minute, second)


def get_date_sort_key(instance):
    """
    Extract a sort key for an instance based on its datetime and precision.
    Handles BCE dates correctly by parsing the datetime string.
    """
    return (parse_date_for_sorting(instance["datetime"]), instance["precision"])


def process_tag_parallel(tag_id):
    """Process a single tag_id in parallel - connects to DB independently"""
    conn = None
    try:
        conn = psycopg2.connect(DB_URI)
        conn.autocommit = False
        result = process_tag(conn, tag_id)
        conn.commit()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error processing tag {tag_id}: {e}")
        return 0
    finally:
        if conn:
            conn.close()


def main_parallel(workers=None):
    """Process all tags in parallel using a process pool"""
    if workers is None:
        workers = max(1, multiprocessing.cpu_count() - 1)  # Default to CPU count - 1

    print(f"Using {workers} worker processes")

    conn = psycopg2.connect(DB_URI)
    tag_ids = []

    try:
        # Count total null story_order rows
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL"
            )
            null_count = cursor.fetchone()[0]
            print(f"Found {null_count} rows with NULL story_order")

        if null_count == 0:
            print("No rows to update. Exiting.")
            return

        # Get all distinct tag_ids with null story_order
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT tag_id 
                FROM tag_instances 
                WHERE story_order IS NULL
                """
            )
            tag_ids = [row[0] for row in cursor.fetchall()]
            print(f"Processing {len(tag_ids)} distinct tags in parallel")

    finally:
        conn.close()

    # Process tags in parallel using a process pool
    with Pool(processes=workers) as pool:
        results = []
        # Use imap_unordered for better load balancing
        for i, result in enumerate(pool.imap_unordered(process_tag_parallel, tag_ids)):
            results.append(result)
            if (i + 1) % 100 == 0 or (i + 1) == len(tag_ids):
                print(f"Completed {i + 1}/{len(tag_ids)} tags")

    total_processed = sum(results)
    print(f"Successfully updated {total_processed} tag_instances")


def process_tag(conn, tag_id):
    """Process all tag_instances for a single tag_id"""
    processed_count = 0
    start_time = datetime.now()
    print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Tag: {tag_id}")
    # Get all tag_instances for this tag_id that need story_order
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        # Get all instances for this tag that need story_order
        query_start = datetime.now()
        cursor.execute(
            """
            SELECT ti.id AS instance_id, ti.summary_id
            FROM tag_instances ti
            WHERE ti.tag_id = %s AND ti.story_order IS NULL
        """,
            (tag_id,),
        )
        query_end = datetime.now()
        print(
            f"[Query 1] Time: {(query_end - query_start).total_seconds():.3f}s - Get instances with NULL story_order"
        )

        instances = cursor.fetchall()
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing {len(instances)} instances"
        )

        if not instances:
            return 0

        # Collect all summary_ids to fetch time data in a single query
        summary_ids = [instance["summary_id"] for instance in instances]

        # Use a single query to get all time data for all summaries
        query_start = datetime.now()
        cursor.execute(
            """
            SELECT DISTINCT ON (ti.summary_id) 
                ti.summary_id, t.datetime, t.precision
            FROM tag_instances ti
            JOIN tags tg ON ti.tag_id = tg.id
            JOIN times t ON tg.id = t.id
            WHERE ti.summary_id = ANY(%s)
            AND tg.type = 'TIME'
        """,
            (summary_ids,),
        )
        query_end = datetime.now()
        print(
            f"[Query 2] Time: {(query_end - query_start).total_seconds():.3f}s - Get time data for {len(summary_ids)} summaries"
        )

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Finished querying times via summaries table."
        )

        # Create a mapping of summary_id to time data
        time_data_by_summary = {}
        for row in cursor.fetchall():
            time_data_by_summary[row["summary_id"]] = {
                "datetime": row["datetime"],
                "precision": row["precision"],
            }

        # Associate each instance with its time data
        instance_data = []
        for instance in instances:
            if instance["summary_id"] in time_data_by_summary:
                time_info = time_data_by_summary[instance["summary_id"]]
                instance_data.append(
                    {
                        "id": instance["instance_id"],
                        "datetime": time_info["datetime"],
                        "precision": time_info["precision"],
                    }
                )

    # Sort instances by datetime first (correctly handling BCE dates), then precision
    sort_start = datetime.now()
    instance_data.sort(key=get_date_sort_key)
    sort_end = datetime.now()
    print(
        f"[Sort] Time: {(sort_end - sort_start).total_seconds():.3f}s - Sorting {len(instance_data)} instances"
    )

    if not instance_data:
        return 0

    # Find the next available story_order for this tag
    with conn.cursor() as cursor:
        query_start = datetime.now()
        cursor.execute(
            """
            SELECT COALESCE(MAX(story_order), 0) 
            FROM tag_instances 
            WHERE tag_id = %s AND story_order IS NOT NULL
        """,
            (tag_id,),
        )
        query_end = datetime.now()
        print(
            f"[Query 3] Time: {(query_end - query_start).total_seconds():.3f}s - Get max story_order"
        )

        max_order = cursor.fetchone()[0]

        # Start at 100000 if no previous story_orders
        curr_order = max_order + 1000 if max_order > 0 else 100000

        # Update each instance with its new story_order
        update_start = datetime.now()
        for i, instance in enumerate(instance_data):
            cursor.execute(
                """
                UPDATE tag_instances 
                SET story_order = %s 
                WHERE id = %s
            """,
                (curr_order, instance["id"]),
            )
            processed_count += 1
            curr_order += 1000
        update_end = datetime.now()
        print(
            f"[Updates] Time: {(update_end - update_start).total_seconds():.3f}s - Updated {len(instance_data)} instances"
        )

    end_time = datetime.now()
    print(
        f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] Finished in {(end_time - start_time).total_seconds()} seconds"
    )
    return processed_count


def reset_all_story_orders():
    """Reset all story_order values to NULL (for testing)"""
    conn = psycopg2.connect(DB_URI)
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE tag_instances SET story_order = NULL")
            count = cursor.rowcount
            print(f"Reset {count} rows to NULL story_order")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error resetting story_order: {e}")
    finally:
        conn.close()


def reset_tag_story_orders(tag_id):
    """Reset story_order values for a specific tag_id to NULL (for testing)"""
    conn = psycopg2.connect(DB_URI)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE tag_instances SET story_order = NULL WHERE tag_id = %s",
                (tag_id,),
            )
            count = cursor.rowcount
            print(f"Reset {count} rows to NULL story_order for tag {tag_id}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error resetting story_order: {e}")
    finally:
        conn.close()


def fix_tag_ordering(conn, tag_id):
    """Fix ordering for a single tag_id"""
    fixed_count = 0

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        # Get all instances for this tag with their time data
        cursor.execute(
            """
            WITH time_data AS (
                SELECT ti.summary_id, t.datetime, t.precision 
                FROM tag_instances ti 
                JOIN tags tg ON ti.tag_id = tg.id 
                JOIN times t ON tg.id = t.id 
                WHERE tg.type = 'TIME'
            )
            SELECT ti.id, ti.story_order, td.datetime, td.precision
            FROM tag_instances ti 
            LEFT JOIN time_data td ON ti.summary_id = td.summary_id 
            WHERE ti.tag_id = %s
            ORDER BY ti.story_order
        """,
            (tag_id,),
        )
        instances = cursor.fetchall()

        # Filter out instances with no time data
        valid_instances = [i for i in instances if i["datetime"] is not None]

        if len(valid_instances) < 2:
            return 0

        # Use custom sorting function to check if instances are already correctly ordered
        sorted_instances = sorted(valid_instances, key=get_date_sort_key)
        is_ordered = all(
            valid_instances[i]["id"] == sorted_instances[i]["id"]
            for i in range(len(valid_instances))
        )

        if not is_ordered:
            # Update each instance one by one to avoid unique constraint issues
            # First, temporarily set all story_orders to negative values
            for i, instance in enumerate(valid_instances):
                temp_order = -1000000 - i  # Use negative values to avoid conflicts
                cursor.execute(
                    """
                    UPDATE tag_instances 
                    SET story_order = %s 
                    WHERE id = %s
                """,
                    (temp_order, instance["id"]),
                )

            # Then set the correct order
            base_order = 100000
            for i, instance in enumerate(sorted_instances):
                new_order = base_order + (i * 1000)
                cursor.execute(
                    """
                    UPDATE tag_instances 
                    SET story_order = %s 
                    WHERE id = %s
                """,
                    (new_order, instance["id"]),
                )
                fixed_count += 1

    return fixed_count


def fix_ordering_issues():
    """Fix instances where events are not in chronological order"""
    conn = psycopg2.connect(DB_URI)
    conn.autocommit = False
    fixed_count = 0

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # First, get all tag_ids that have more than one tag_instance
            cursor.execute(
                """
                SELECT tag_id, COUNT(*) 
                FROM tag_instances 
                GROUP BY tag_id 
                HAVING COUNT(*) > 1
            """
            )
            tag_ids = [row[0] for row in cursor.fetchall()]
            print(f"Checking ordering for {len(tag_ids)} tags with multiple instances")

            for idx, tag_id in enumerate(tag_ids):
                tag_fixed = fix_tag_ordering(conn, tag_id)
                fixed_count += tag_fixed

                # Commit every 100 tags to avoid long transactions
                if (idx + 1) % 100 == 0:
                    conn.commit()
                    print(
                        f"Checked {idx + 1}/{len(tag_ids)} tags, fixed {fixed_count} instances"
                    )

        conn.commit()
        print(f"Fixed ordering for {fixed_count} instances")

    except Exception as e:
        conn.rollback()
        print(f"Error fixing ordering: {e}")
        raise
    finally:
        conn.close()

    return fixed_count


def fix_specific_tag(tag_id):
    """Fix ordering for a specific tag_id"""
    conn = psycopg2.connect(DB_URI)
    conn.autocommit = False

    try:
        fixed = fix_tag_ordering(conn, tag_id)
        conn.commit()
        print(f"Fixed {fixed} instances for tag {tag_id}")
    except Exception as e:
        conn.rollback()
        print(f"Error fixing tag {tag_id}: {e}")
    finally:
        conn.close()


def verify_tag_ordering(tag_id):
    """Verify the ordering of a specific tag_id"""
    conn = psycopg2.connect(DB_URI)

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                """
                WITH time_data AS (
                    SELECT ti.summary_id, t.datetime, t.precision 
                    FROM tag_instances ti 
                    JOIN tags tg ON ti.tag_id = tg.id 
                    JOIN times t ON tg.id = t.id 
                    WHERE tg.type = 'TIME'
                )
                SELECT ti.id, ti.story_order, td.datetime, td.precision
                FROM tag_instances ti 
                LEFT JOIN time_data td ON ti.summary_id = td.summary_id 
                WHERE ti.tag_id = %s
                ORDER BY ti.story_order
            """,
                (tag_id,),
            )

            instances = cursor.fetchall()
            valid_instances = [i for i in instances if i["datetime"] is not None]

            print(
                f"Found {len(instances)} instances for tag {tag_id}, {len(valid_instances)} with time data"
            )

            if len(valid_instances) < 2:
                print("Not enough instances with time data to verify ordering")
                return

            # Use custom sorting function to check if instances are correctly ordered
            sorted_instances = sorted(valid_instances, key=get_date_sort_key)
            ordered_correctly = all(
                valid_instances[i]["id"] == sorted_instances[i]["id"]
                for i in range(len(valid_instances))
            )

            if not ordered_correctly:
                print(f"Ordering issue found:")
                for i in range(len(valid_instances)):
                    if valid_instances[i]["id"] != sorted_instances[i]["id"]:
                        curr = valid_instances[i]
                        expected = sorted_instances[i]
                        print(f"  Position {i}:")
                        print(
                            f"    Current: ID {curr['id']}: {curr['datetime']} (precision {curr['precision']})"
                        )
                        print(
                            f"    Expected: ID {expected['id']}: {expected['datetime']} (precision {expected['precision']})"
                        )
            else:
                print("All instances are correctly ordered by datetime and precision")

            # Print the current ordering
            print("\nCurrent ordering:")
            for i, instance in enumerate(valid_instances):
                date_components = parse_date_for_sorting(instance["datetime"])
                year_str = (
                    date_components[0] if date_components[0] != float("inf") else "N/A"
                )
                print(
                    f"{i+1}. ID: {instance['id']}, Story Order: {instance['story_order']}, "
                    f"Date: {instance['datetime']}, Precision: {instance['precision']}, "
                    f"Parsed Year: {year_str}"
                )

    except Exception as e:
        print(f"Error verifying tag ordering: {e}")
    finally:
        conn.close()


def verify_random_tags(count=3):
    """Verify ordering for a random sample of tags"""
    conn = psycopg2.connect(DB_URI)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT tag_id FROM tag_instances 
                GROUP BY tag_id 
                HAVING COUNT(*) > 5 
                ORDER BY RANDOM() 
                LIMIT {count}
            """
            )
            random_tags = [row[0] for row in cursor.fetchall()]

        print(f"Verifying {len(random_tags)} random tags")
        for i, tag_id in enumerate(random_tags):
            print(f"\n{'='*50}\nTag {i+1}/{len(random_tags)}: {tag_id}\n{'-'*50}")
            verify_tag_ordering(tag_id)
    except Exception as e:
        print(f"Error getting random tags: {e}")
    finally:
        conn.close()


def main():
    """Process all tags sequentially (original implementation)"""
    conn = psycopg2.connect(DB_URI)
    conn.autocommit = False

    try:
        # Count total null story_order rows
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM tag_instances WHERE story_order IS NULL"
            )
            null_count = cursor.fetchone()[0]
            print(f"Found {null_count} rows with NULL story_order")

        if null_count == 0:
            print("No rows to update. Exiting.")
            return

        # Get all distinct tag_ids with null story_order
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT tag_id 
                FROM tag_instances 
                WHERE story_order IS NULL
            """
            )
            tag_ids = [row[0] for row in cursor.fetchall()]
            print(f"Processing {len(tag_ids)} distinct tags")

        # Process each tag_id
        total_processed = 0
        for idx, tag_id in enumerate(tag_ids):
            processed = process_tag(conn, tag_id)
            total_processed += processed

            # Commit every 1000 tags to avoid long transactions
            if (idx + 1) % 1000 == 0:
                conn.commit()
                print(
                    f"Committed {idx + 1}/{len(tag_ids)} tags, {total_processed} instances"
                )

        # Final commit
        conn.commit()
        print(f"Successfully updated {total_processed} tag_instances")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update or fix story_order values in tag_instances table"
    )

    # Add mutually exclusive group for operations
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--update-all", action="store_true", help="Update all NULL story_order values"
    )
    group.add_argument(
        "--reset-all", action="store_true", help="Reset all story_orders to NULL"
    )
    group.add_argument(
        "--fix-all", action="store_true", help="Fix ordering issues for all tags"
    )
    group.add_argument(
        "--verify",
        action="store_true",
        help="Verify ordering for random sample of tags",
    )
    group.add_argument("--tag", type=str, help="Fix ordering for a specific tag_id")
    group.add_argument(
        "--verify-tag", type=str, help="Verify ordering for a specific tag_id"
    )
    group.add_argument(
        "--reset-tag", type=str, help="Reset story_order for a specific tag_id"
    )

    # Add optional workers argument for parallel processing
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of worker processes for parallel execution (default: CPU count - 1)",
    )

    args = parser.parse_args()

    start_time = time.time()

    # Default action is to fix all ordering issues
    if args.update_all:
        if args.workers is not None:
            main_parallel(args.workers)
        else:
            main_parallel()
    elif args.reset_all:
        reset_all_story_orders()
    elif args.tag:
        fix_specific_tag(args.tag)
    elif args.verify_tag:
        verify_tag_ordering(args.verify_tag)
    elif args.reset_tag:
        reset_tag_story_orders(args.reset_tag)
    elif args.verify:
        verify_random_tags(5)
    else:
        # Default action
        fix_ordering_issues()

    elapsed = time.time() - start_time
    print(f"\nScript completed in {elapsed:.2f} seconds")
