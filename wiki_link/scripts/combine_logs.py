#!/usr/bin/env python
"""
Script to combine multiple WikiLink log files into a single file while preserving chronological order.

Usage:
    python combine_logs.py [input_directory] [output_file]

If no arguments are provided, it will:
- Look for log files in the current directory
- Output to combined_wikilink.log
"""

import sys
import os
import glob
from datetime import datetime
from typing import List, Tuple

# Pattern to match timestamp in log lines
TIMESTAMP_PATTERN = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"


def extract_timestamp(line: str) -> Tuple[datetime, str]:
    """Extract timestamp from log line and return (timestamp, line) tuple."""
    import re

    match = re.search(TIMESTAMP_PATTERN, line)
    if match:
        try:
            timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S,%f")
            return timestamp, line
        except ValueError:
            # If timestamp parsing fails, return a very old date to put these lines at the start
            return datetime.min, line
    return datetime.min, line


def combine_logs(
    input_dir: str = ".", output_file: str = "combined_wikilink.log"
) -> None:
    """Combine all wikilink_*.log files in input_dir into a single output file."""
    # Find all log files
    log_files = glob.glob(os.path.join(input_dir, "wikilink_*.log"))
    if not log_files:
        print(f"No log files found in {input_dir}")
        return

    print(f"Found {len(log_files)} log files to combine")

    # Read all lines from all files
    all_lines: List[Tuple[datetime, str]] = []
    for log_file in log_files:
        try:
            with open(log_file, "r") as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        all_lines.append(extract_timestamp(line))
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
            continue

    # Sort lines by timestamp
    all_lines.sort(key=lambda x: x[0])

    # Write sorted lines to output file
    try:
        with open(output_file, "w") as f:
            for _, line in all_lines:
                f.write(line)
        print(f"Successfully combined logs into {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")


def main():
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "combined_wikilink.log"

    combine_logs(input_dir, output_file)


if __name__ == "__main__":
    main()
