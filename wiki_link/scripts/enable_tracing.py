#!/usr/bin/env python
"""
Script to enable tracing in the WikiLink service.

This script can be used to enable or disable tracing, and configures file logging.
It's useful for temporarily enabling tracing in a running application.

Usage:
    # Enable tracing with 100ms threshold, writing to logs directory
    python enable_tracing.py --enable --threshold 100 --file-logging

    # Enable with custom log file
    python enable_tracing.py --enable --file-logging --log-file /tmp/wiki_tracing.log

    # Disable tracing
    python enable_tracing.py --disable

Example for deployment:
    export WIKI_LINK_TRACING_ENABLED=true
    export WIKI_LINK_TRACING_THRESHOLD_MS=100
    export WIKI_LINK_FILE_LOGGING=true
    export WIKI_LINK_LOG_FILE=/var/log/wiki_link/tracing.log
"""

import argparse
import os
import sys
import logging

# Add parent directory to path so we can import the tracing module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from wiki_service.tracing import configure_tracing


def get_default_log_path():
    """Get a sensible default log path based on the script location"""
    # Get the absolute path to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Create a logs directory in the project root
    logs_dir = os.path.join(project_root, "logs")

    # Return a path in the logs directory
    return os.path.join(logs_dir, "wiki_link_tracing.log")


def main():
    parser = argparse.ArgumentParser(description="Configure WikiLink tracing")

    # Basic configuration
    parser.add_argument("--enable", action="store_true", help="Enable tracing")
    parser.add_argument("--disable", action="store_true", help="Disable tracing")
    parser.add_argument(
        "--threshold", type=float, help="Threshold in milliseconds above which to log"
    )

    # File logging configuration
    parser.add_argument(
        "--file-logging", action="store_true", help="Enable file logging"
    )
    parser.add_argument(
        "--no-file-logging", action="store_true", help="Disable file logging"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help=f"Path to log file (default: {get_default_log_path()})",
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure root logger to see messages
    logging.basicConfig(level=logging.INFO)

    # Set default log file if not specified
    if args.file_logging and not args.log_file:
        args.log_file = get_default_log_path()

    # Build configuration parameters
    config_params = {}

    if args.enable and args.disable:
        print("Error: Cannot specify both --enable and --disable")
        sys.exit(1)

    if args.enable:
        config_params["enabled"] = True
    elif args.disable:
        config_params["enabled"] = False

    if args.threshold is not None:
        config_params["threshold_ms"] = args.threshold

    if args.file_logging and args.no_file_logging:
        print("Error: Cannot specify both --file-logging and --no-file-logging")
        sys.exit(1)

    if args.file_logging:
        config_params["file_logging"] = True
    elif args.no_file_logging:
        config_params["file_logging"] = False

    if args.log_file:
        config_params["log_file"] = args.log_file

    # Apply configuration
    if config_params:
        configure_tracing(**config_params)
        print("Tracing configuration updated")
    else:
        print(
            "No configuration parameters specified. Run with --help for usage information."
        )

    # Print environment variable configuration for deployment
    print("\nTo configure tracing via environment variables:")
    print(
        "export WIKI_LINK_TRACING_ENABLED=",
        (
            "true"
            if args.enable
            else "false" if args.disable else "${WIKI_LINK_TRACING_ENABLED:-false}"
        ),
    )

    if args.threshold is not None:
        print(f"export WIKI_LINK_TRACING_THRESHOLD_MS={args.threshold}")

    if args.file_logging:
        print("export WIKI_LINK_FILE_LOGGING=true")
    elif args.no_file_logging:
        print("export WIKI_LINK_FILE_LOGGING=false")

    if args.log_file:
        print(f"export WIKI_LINK_LOG_FILE={args.log_file}")


if __name__ == "__main__":
    main()
