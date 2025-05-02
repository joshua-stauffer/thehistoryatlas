#!/usr/bin/env python

import argparse
import uuid
from typing import Optional

from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate story order for tag instances within a specified tag ID range."
    )

    parser.add_argument(
        "--start-tag-id",
        type=lambda x: uuid.UUID(x) if x else None,
        default=None,
        help="Optional UUID to start processing from (inclusive)",
    )

    parser.add_argument(
        "--stop-tag-id",
        type=lambda x: uuid.UUID(x) if x else None,
        default=None,
        help="Optional UUID to stop processing at (inclusive)",
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="Number of threads to use for parallel processing",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Set up the app manager and get access to the history app
    config_app = Config()
    app_manager = AppManager(config_app=config_app)
    history_app = app_manager.history_app

    # Call calculate_story_order_range with the command line arguments
    history_app.calculate_story_order_range(
        start_tag_id=args.start_tag_id,
        stop_tag_id=args.stop_tag_id,
        num_workers=args.num_workers,
    )


if __name__ == "__main__":
    main()
