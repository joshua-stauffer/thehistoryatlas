#!/usr/bin/env python3
import re
from collections import defaultdict
from pathlib import Path
import statistics
import argparse
import json


def parse_trace_line(line):
    """Parse a trace log line into its components."""
    # Example line format:
    # 2024-03-19 10:15:30,123 - history_trace - DEBUG - create_wikidata_event:duration_seconds:0.123456
    match = re.search(r"DEBUG - ([^:]+):duration_seconds:(\d+\.\d+)", line)
    if match:
        operation = match.group(1)
        duration = float(match.group(2))
        return {"type": "standard", "operation": operation, "duration": duration}

    # Example DB operation format:
    # DEBUG - db_op:create_tag_instance:class:Repository:called_from:history_app.create_wikidata_event:duration_seconds:0.123456
    db_match = re.search(
        r"DEBUG - db_op:([^:]+):class:([^:]+):called_from:([^:]+):duration_seconds:(\d+\.\d+)",
        line,
    )
    if db_match:
        operation = db_match.group(1)
        class_name = db_match.group(2)
        caller = db_match.group(3)
        duration = float(db_match.group(4))
        return {
            "type": "db_op",
            "operation": operation,
            "class": class_name,
            "caller": caller,
            "duration": duration,
        }

    return None


def analyze_traces(log_file):
    """Analyze trace logs and return statistics."""
    standard_durations = defaultdict(list)
    db_durations = defaultdict(list)
    db_calls_by_parent = defaultdict(lambda: defaultdict(list))

    with open(log_file, "r") as f:
        for line in f:
            result = parse_trace_line(line)
            if not result:
                continue

            if result["type"] == "standard":
                standard_durations[result["operation"]].append(result["duration"])
            elif result["type"] == "db_op":
                db_durations[result["operation"]].append(result["duration"])
                db_calls_by_parent[result["caller"]][result["operation"]].append(
                    result["duration"]
                )

    stats = {
        "standard": compute_stats(standard_durations),
        "db_operations": compute_stats(db_durations),
        "db_calls_by_parent": {
            parent: compute_stats(operations)
            for parent, operations in db_calls_by_parent.items()
        },
    }

    return stats


def compute_stats(durations_dict):
    """Compute statistics for a dictionary of durations."""
    stats = {}
    for operation, times in durations_dict.items():
        stats[operation] = {
            "count": len(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "total": sum(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
        }
    return stats


def print_stats(stats):
    """Print statistics in a formatted way."""
    print("\nPerformance Analysis Report")
    print("=" * 80)

    # Print standard operations
    print("\nSTANDARD OPERATIONS")
    print("-" * 80)
    sorted_ops = sorted(
        stats["standard"].items(), key=lambda x: x[1]["total"], reverse=True
    )
    print_operation_stats(sorted_ops)

    # Print database operations
    print("\nDATABASE OPERATIONS (Overall)")
    print("-" * 80)
    sorted_db_ops = sorted(
        stats["db_operations"].items(), key=lambda x: x[1]["total"], reverse=True
    )
    print_operation_stats(sorted_db_ops)

    # Print database operations by parent
    print("\nDATABASE OPERATIONS (By Caller)")
    print("-" * 80)
    for parent, operations in stats["db_calls_by_parent"].items():
        print(f"\nCaller: {parent}")
        print("-" * 60)
        sorted_parent_ops = sorted(
            operations.items(), key=lambda x: x[1]["total"], reverse=True
        )
        print_operation_stats(sorted_parent_ops, indent="  ")


def print_operation_stats(operations, indent=""):
    """Print statistics for a list of operations."""
    for operation, metrics in operations:
        print(f"\n{indent}Operation: {operation}")
        print(f"{indent}{'-' * 40}")
        print(f"{indent}Call count:     {metrics['count']:>10,}")
        print(f"{indent}Total time:     {metrics['total']:>10.3f} seconds")
        print(f"{indent}Average time:   {metrics['avg']:>10.3f} seconds")
        print(f"{indent}Median time:    {metrics['median']:>10.3f} seconds")
        print(f"{indent}Min time:       {metrics['min']:>10.3f} seconds")
        print(f"{indent}Max time:       {metrics['max']:>10.3f} seconds")
        print(f"{indent}Std deviation:  {metrics['std_dev']:>10.3f} seconds")


def generate_optimization_suggestions(stats):
    """Generate optimization suggestions based on stats."""
    suggestions = []

    # Identify the most expensive operation
    main_ops = stats["standard"]
    sorted_ops = sorted(main_ops.items(), key=lambda x: x[1]["total"], reverse=True)

    if len(sorted_ops) > 0:
        top_op_name, top_op = sorted_ops[0]

        # Check if create_tag_instances is the bottleneck
        if top_op_name == "create_tag_instances" and top_op["total"] > 0:
            # Look at the specific database operations
            db_ops = stats["db_operations"]

            # Check for update_story_orders performance
            if (
                "update_story_orders" in db_ops
                and db_ops["update_story_orders"]["total"] > 0.3 * top_op["total"]
            ):
                suggestions.append(
                    "The update_story_orders operation is consuming a significant portion of time. "
                    "Consider optimizing the story_order update logic or implementing batch updates."
                )

            # Check for tag_instance insertion performance
            if (
                "execute_tag_instance_insert" in db_ops
                and db_ops["execute_tag_instance_insert"]["avg"] > 0.1
            ):
                suggestions.append(
                    "Tag instance insertions are slow. Consider implementing batch inserts "
                    "instead of individual inserts, or check for missing indexes."
                )

            # Check if there's a uniqueness constraint enforcement overhead
            if top_op["std_dev"] / top_op["avg"] > 0.5:
                suggestions.append(
                    "High variance in tag_instance creation suggests potential contention "
                    "or deadlocks. Check for uniqueness constraint enforcement overhead."
                )

        # Suggestions for any operation that takes too long
        if top_op["avg"] > 1.0:
            suggestions.append(
                f"The {top_op_name} operation takes an average of {top_op['avg']:.2f} seconds. "
                f"Consider optimizing it or making it asynchronous if possible."
            )

    # Identify slow database operations
    db_ops = stats["db_operations"]
    slow_db_ops = [
        (name, op)
        for name, op in db_ops.items()
        if op["avg"] > 0.2 or op["total"] > 5.0
    ]

    for name, op in slow_db_ops:
        if name == "get_story_order":
            suggestions.append(
                "The get_story_order database operation is slow. Consider caching story orders "
                "or implementing a more efficient algorithm to compute them."
            )
        elif name == "update_story_orders":
            suggestions.append(
                "Updating story orders is expensive. Consider batching updates or using "
                "an alternative approach to sequence management that doesn't require reordering."
            )

    # Check transaction patterns
    if "commit_transaction" in main_ops and main_ops["commit_transaction"]["count"] > 0:
        avg_commit_time = main_ops["commit_transaction"]["avg"]
        if avg_commit_time > 0.1:
            suggestions.append(
                f"Transactions take an average of {avg_commit_time:.2f} seconds to commit. "
                f"Consider reducing transaction size or optimizing your database configuration."
            )

    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Analyze history trace logs")
    parser.add_argument(
        "--log-file",
        default=str(Path(__file__).parent.parent / "logs" / "history_trace.log"),
        help="Path to the trace log file",
    )
    parser.add_argument(
        "--output-json",
        help="Path to save analysis results as JSON",
    )

    args = parser.parse_args()

    try:
        stats = analyze_traces(args.log_file)
        print_stats(stats)

        print("\nOPTIMIZATION SUGGESTIONS")
        print("=" * 80)
        suggestions = generate_optimization_suggestions(stats)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion}")

        if args.output_json:
            # Convert stats to JSON serializable format
            json_stats = {
                "standard": stats["standard"],
                "db_operations": stats["db_operations"],
                "db_calls_by_parent": stats["db_calls_by_parent"],
                "optimization_suggestions": suggestions,
            }
            with open(args.output_json, "w") as f:
                json.dump(json_stats, f, indent=2)
            print(f"\nAnalysis saved to {args.output_json}")

    except FileNotFoundError:
        print(f"Error: Log file not found at {args.log_file}")
        print("Please run some operations first to generate trace logs.")
    except Exception as e:
        print(f"Error analyzing traces: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
