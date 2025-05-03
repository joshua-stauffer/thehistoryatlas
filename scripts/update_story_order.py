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
    python update_story_order.py --reset-all    # Reset all story_orders to NULL
    python update_story_order.py --verify       # Verify ordering for random sample of tags
    python update_story_order.py --tag TAG_ID   # Fix ordering for a specific tag
    python update_story_order.py --verify-tag TAG_ID  # Verify ordering for a specific tag
    python update_story_order.py --reset-tag TAG_ID   # Reset story_orders for a specific tag

Connection string: postgresql://postgres:4f6WxSSoYVSWTVp3QVovWnzLTeCkj9HZ@localhost:5432
"""
import psycopg2
import psycopg2.extras
import time
import argparse
from collections import defaultdict
import uuid

# Register UUID adapter for PostgreSQL
psycopg2.extras.register_uuid()

# Database connection string
DB_URI = "postgresql://postgres:4f6WxSSoYVSWTVp3QVovWnzLTeCkj9HZ@localhost:5432"


def main():
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


def process_tag(conn, tag_id):
    """Process all tag_instances for a single tag_id"""
    processed_count = 0

    # Get all tag_instances for this tag_id that need story_order
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        # Get all instances for this tag that need story_order
        cursor.execute(
            """
            SELECT ti.id AS instance_id, ti.summary_id
            FROM tag_instances ti
            WHERE ti.tag_id = %s AND ti.story_order IS NULL
        """,
            (tag_id,),
        )
        instances = cursor.fetchall()

        if not instances:
            return 0

        # Collect all summary_ids to fetch time data in a single query
        summary_ids = [instance["summary_id"] for instance in instances]

        # Use a single query to get all time data for all summaries
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

    # Sort instances by datetime first, then precision
    instance_data.sort(key=lambda x: (x["datetime"], x["precision"]))

    if not instance_data:
        return 0

    # Find the next available story_order for this tag
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT MAX(story_order) 
            FROM tag_instances 
            WHERE tag_id = %s AND story_order IS NOT NULL
        """,
            (tag_id,),
        )
        max_order = cursor.fetchone()[0]

        # Start at 100000 if no previous story_orders
        curr_order = max_order + 1000 if max_order is not None else 100000

        # Update each instance with its new story_order
        for instance in instance_data:
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

        # Check if instances are already correctly ordered by datetime
        is_ordered = all(
            valid_instances[i]["datetime"] <= valid_instances[i + 1]["datetime"]
            or (
                valid_instances[i]["datetime"] == valid_instances[i + 1]["datetime"]
                and valid_instances[i]["precision"]
                <= valid_instances[i + 1]["precision"]
            )
            for i in range(len(valid_instances) - 1)
        )

        if not is_ordered:
            # Sort instances by datetime, then precision
            sorted_instances = sorted(
                valid_instances, key=lambda x: (x["datetime"], x["precision"])
            )

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

            # Check if instances are correctly ordered by datetime
            ordered_correctly = True
            for i in range(len(valid_instances) - 1):
                curr = valid_instances[i]
                next_inst = valid_instances[i + 1]
                if curr["datetime"] > next_inst["datetime"] or (
                    curr["datetime"] == next_inst["datetime"]
                    and curr["precision"] > next_inst["precision"]
                ):
                    ordered_correctly = False
                    print(f"Ordering issue found:")
                    print(
                        f"  Instance {curr['id']}: {curr['datetime']} (precision {curr['precision']}) at position {i}"
                    )
                    print(
                        f"  Instance {next_inst['id']}: {next_inst['datetime']} (precision {next_inst['precision']}) at position {i+1}"
                    )

            if ordered_correctly:
                print("All instances are correctly ordered by datetime and precision")

            # Print the current ordering
            print("\nCurrent ordering:")
            for i, instance in enumerate(valid_instances):
                print(
                    f"{i+1}. ID: {instance['id']}, Story Order: {instance['story_order']}, Date: {instance['datetime']}, Precision: {instance['precision']}"
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
        "--reset-all", action="store_true", help="Reset all story_order values to NULL"
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

    args = parser.parse_args()

    start_time = time.time()

    # Default action is to fix all ordering issues
    if args.update_all:
        main()
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
