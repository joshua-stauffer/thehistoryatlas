#!/usr/bin/env python
"""
Script to analyze trace logs from WikiLink service.

This script reads trace logs from stdin or a file and summarizes the performance data.

Usage:
    python analyze_traces.py [logfile]
    cat logfile | python analyze_traces.py

If no logfile is provided, input is read from stdin.
"""

import sys
import re
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

TRACE_PATTERN = re.compile(r"TRACE: (.+) took ([\d.]+)ms")


def analyze_traces(lines):
    # Collect data by function
    data: Dict[str, List[float]] = defaultdict(list)

    for line in lines:
        match = TRACE_PATTERN.search(line)
        if match:
            func_name, duration_str = match.groups()
            duration = float(duration_str)
            data[func_name].append(duration)

    # Calculate statistics
    stats = []
    for func_name, durations in data.items():
        avg = statistics.mean(durations)
        if len(durations) > 1:
            stddev = statistics.stdev(durations)
        else:
            stddev = 0
        median = statistics.median(durations)
        min_val = min(durations)
        max_val = max(durations)
        count = len(durations)
        total = sum(durations)

        stats.append((func_name, avg, median, min_val, max_val, stddev, count, total))

    # Sort by total time (highest impact first)
    stats.sort(key=lambda x: x[7], reverse=True)

    return stats


def print_report(stats):
    print("\nWikiLink Trace Analysis Report")
    print("============================\n")

    # Print summary table
    print(
        f"{'Function':<50} {'Avg (ms)':<10} {'Median':<10} {'Min':<10} {'Max':<10} {'StdDev':<10} {'Count':<8} {'Total (ms)':<12}"
    )
    print("-" * 120)

    for func_name, avg, median, min_val, max_val, stddev, count, total in stats:
        print(
            f"{func_name:<50} {avg:<10.2f} {median:<10.2f} {min_val:<10.2f} {max_val:<10.2f} {stddev:<10.2f} {count:<8} {total:<12.2f}"
        )

    # Print summary
    total_time = sum(stat[7] for stat in stats)
    total_calls = sum(stat[6] for stat in stats)
    print("\nSummary:")
    print(f"Total traced time: {total_time:.2f}ms")
    print(f"Total function calls: {total_calls}")

    # Top 5 slowest functions
    print("\nTop 5 slowest individual calls:")
    slowest = sorted(
        [(func_name, max_val) for func_name, _, _, _, max_val, _, _, _ in stats],
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    for func_name, duration in slowest:
        print(f"{func_name}: {duration:.2f}ms")

    # Most impactful functions
    print("\nTop 5 most impactful functions (by total time):")
    for func_name, _, _, _, _, _, count, total in stats[:5]:
        print(
            f"{func_name}: {total:.2f}ms ({count} calls, {total/total_time*100:.1f}% of total time)"
        )


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    stats = analyze_traces(lines)
    print_report(stats)


if __name__ == "__main__":
    main()
