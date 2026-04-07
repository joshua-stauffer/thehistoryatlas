#!/usr/bin/env python3
"""CLI tool for extracting historical events from PDFs using Claude."""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from text_reader.claude_client import ClaudeClient
from text_reader.config import Config
from text_reader.extractor import run_batch_pipeline, run_pipeline, run_resume_pipeline
from text_reader.geonames import GeoNamesClient
from text_reader.rest_client import RestClient


def main():
    parser = argparse.ArgumentParser(
        description="Extract historical events from PDFs using Claude"
    )
    parser.add_argument(
        "--file", default=None, help="Path to the PDF file (required unless --resume-batch)"
    )
    parser.add_argument(
        "--title", default=None, help="Book title (required unless --resume-batch)"
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
        default="sonnet",
        choices=["haiku", "sonnet", "opus"],
        help="Claude model to use (default: sonnet)",
    )
    parser.add_argument(
        "--start-page", type=int, default=1, help="Start page (default: 1)"
    )
    parser.add_argument(
        "--end-page", type=int, default=None, help="End page (default: all)"
    )
    parser.add_argument(
        "--pdf-offset",
        type=int,
        default=0,
        help=(
            "Offset from PDF page number to printed book page number "
            "(book_page = pdf_page - pdf_offset). "
            "E.g. if PDF page 15 = book page 1, use --pdf-offset 14. "
            "Default: 0 (PDF pages match book pages)."
        ),
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
        "--batch",
        action="store_true",
        help="Use the Anthropic Message Batches API (50%% discount, no interactive review)",
    )
    parser.add_argument(
        "--resume-batch",
        metavar="STATE_FILE",
        default=None,
        help="Resume a batch run from a saved state file (created automatically on batch submission)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    slug = re.sub(r"[^\w]+", "_", args.title.lower()).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{timestamp}_{slug}.log"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    logging.getLogger(__name__).info(f"Logging to {log_path}")

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
    if args.resume_batch:
        pass  # file/title not needed for resume
    elif not args.file or not args.title:
        parser.error("--file and --title are required unless --resume-batch is used")

    if args.resume_batch:
        run_resume_pipeline(
            state_file=args.resume_batch,
            rest_client=rest_client,
            claude_client=claude_client,
            geonames_client=geonames_client,
        )
        return

    pipeline_kwargs = dict(
        file_path=args.file,
        title=args.title,
        author=args.author,
        publisher_name=args.publisher,
        pub_date=args.pub_date,
        model=args.model,
        start_page=args.start_page,
        end_page=args.end_page,
        pdf_page_offset=args.pdf_offset,
        rest_client=rest_client,
        claude_client=claude_client,
        geonames_client=geonames_client,
    )
    if args.batch:
        run_batch_pipeline(**pipeline_kwargs)
    else:
        run_pipeline(skip_review=args.skip_review, **pipeline_kwargs)


if __name__ == "__main__":
    main()
