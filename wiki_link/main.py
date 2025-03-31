#!/usr/bin/env python3

import argparse
import logging
from typing import Optional

from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database
from wiki_service.wikidata_query_service import WikiDataQueryService
from wiki_service.wiki_service import WikiService
from wiki_service.rest_client import RestClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def create_wiki_service() -> WikiService:
    """Create and configure a WikiService instance."""
    config = WikiServiceConfig()
    database = Database(config)
    wikidata_query_service = WikiDataQueryService(config)
    rest_client = RestClient(config)

    return WikiService(
        wikidata_query_service=wikidata_query_service,
        database=database,
        config=config,
        rest_client=rest_client,
    )


def main(num_people: Optional[int] = None, num_works: Optional[int] = None) -> None:
    """
    Main entry point for the WikiService application.

    Args:
        num_people: Optional number of people to process. If None, processes all available.
        num_works: Optional number of works of art to process. If None, processes none.
    """
    service = create_wiki_service()
    service.run(num_people=num_people, num_works=num_works)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the WikiService to process people and create events."
    )
    parser.add_argument(
        "--num-people",
        type=int,
        help="Number of people to process. If not specified, processes all available.",
        required=False,
    )
    parser.add_argument(
        "--works-of-art",
        type=int,
        help="Number of works of art to process. If not specified, processes none.",
        required=False,
        dest="num_works",
    )

    args = parser.parse_args()
    main(num_people=args.num_people, num_works=args.num_works)
