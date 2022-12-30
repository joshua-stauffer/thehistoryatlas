from dataclasses import asdict
from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable, Literal, Awaitable


log = getLogger(__name__)
log.setLevel("DEBUG")


class GQLApi:
    def __init__(
        self,
        # application callbacks
    ):
        pass

    def get_schema(self) -> Schema:
        """Output a GraphQL Schema."""

        @strawberry.type
        class Query:
            status: str = strawberry.field(resolver=self._status_handler)

        return Schema(query=Query, enable_federation_2=True)

    def _status_handler(self) -> str:
        log.info("Received status request - responding OK.")
        return "OK"
