#!/usr/bin/env python3
"""CLI tool for extracting historical events from PDFs using Claude."""

import argparse
import logging
import sys

from text_reader.claude_client import ClaudeClient
from text_reader.config import Config
from text_reader.extractor import run_pipeline
from text_reader.geonames import GeoNamesClient
from text_reader.rest_client import RestClient


def main():
    parser = argparse.ArgumentParser(
        description="Extract historical events from PDFs using Claude"
    )
    parser.add_argument(
        "--file", required=True, help="Path to the PDF file"
    )
    parser.add_argument(
        "--title", required=True, help="Book title"
    )
    parser.add_argument(
        "--author", required=True, help="Book author"
    )
    parser.add_argument(
        "--publisher", default="Unknown", help="Publisher name"
    )
    parser.add_argument(
        "--pub-date", default=None, help="Publication date"
    )
    parser.add_argument(
        "--model",
        default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help="Claude model to use (default: haiku)",
    )
    parser.add_argument(
        "--start-page", type=int, default=1, help="Start page (default: 1)"
    )
    parser.add_argument(
        "--end-page", type=int, default=None, help="End page (default: all)"
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Skip human review of each event",
    )
    parser.add_argument(
        "--server-url",
        default=None,
        help="Server URL (overrides THA_SERVER_URL env var)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Load config
    try:
        config = Config()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    server_url = args.server_url or config.server_url

    # Initialize clients
    rest_client = RestClient(
        base_url=server_url, api_key=config.tha_api_key
    )
    claude_client = ClaudeClient(
        api_key=config.claude_api_key, model=args.model
    )
    geonames_client = GeoNamesClient(username=config.geonames_username)

    print(f"Text Reader CLI")
    print(f"  Server: {server_url}")
    print(f"  Model:  {args.model}")
    print(f"  File:   {args.file}")
    if geonames_client.available:
        print(f"  GeoNames: enabled")
    print()

    # Run pipeline
    run_pipeline(
        file_path=args.file,
        title=args.title,
        author=args.author,
        publisher_name=args.publisher,
        pub_date=args.pub_date,
        model=args.model,
        start_page=args.start_page,
        end_page=args.end_page,
        skip_review=args.skip_review,
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )


if __name__ == "__main__":
    main()
