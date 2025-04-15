#!/usr/bin/env python3
import re
from collections import defaultdict
from pathlib import Path
import statistics
import argparse


def parse_trace_line(line):
    """Parse a trace log line into its components."""
    # Example line format:
    # 2024-03-19 10:15:30,123 - history_trace - DEBUG - create_wikidata_event:duration_seconds:0.123456
    match = re.search(r"DEBUG - ([^:]+):duration_seconds:(\d+\.\d+)", line)
    if match:
        operation = match.group(1)
        duration = float(match.group(2))
        return operation, duration
    return None


def analyze_traces(log_file):
    """Analyze trace logs and return statistics."""
    durations = defaultdict(list)

    with open(log_file, "r") as f:
        for line in f:
            result = parse_trace_line(line)
            if result:
                operation, duration = result
                durations[operation].append(duration)

    stats = {}
    for operation, times in durations.items():
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

    # Sort operations by total time spent
    sorted_ops = sorted(stats.items(), key=lambda x: x[1]["total"], reverse=True)

    for operation, metrics in sorted_ops:
        print(f"\nOperation: {operation}")
        print("-" * 40)
        print(f"Call count:     {metrics['count']:>10,}")
        print(f"Total time:     {metrics['total']:>10.3f} seconds")
        print(f"Average time:   {metrics['avg']:>10.3f} seconds")
        print(f"Median time:    {metrics['median']:>10.3f} seconds")
        print(f"Min time:       {metrics['min']:>10.3f} seconds")
        print(f"Max time:       {metrics['max']:>10.3f} seconds")
        print(f"Std deviation:  {metrics['std_dev']:>10.3f} seconds")

        # Calculate percentage of total time if this is a sub-operation
        if operation != "create_wikidata_event":
            total_time = stats.get("create_wikidata_event", {}).get("total", 0)
            if total_time > 0:
                percentage = (metrics["total"] / total_time) * 100
                print(f"% of total:     {percentage:>9.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Analyze history trace logs")
    parser.add_argument(
        "--log-file",
        default=str(Path(__file__).parent.parent / "logs" / "history_trace.log"),
        help="Path to the trace log file",
    )

    args = parser.parse_args()

    try:
        stats = analyze_traces(args.log_file)
        print_stats(stats)
    except FileNotFoundError:
        print(f"Error: Log file not found at {args.log_file}")
        print("Please run some operations first to generate trace logs.")
    except Exception as e:
        print(f"Error analyzing traces: {e}")


if __name__ == "__main__":
    main()
