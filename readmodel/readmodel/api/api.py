from dataclasses import asdict
from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable, Literal, Awaitable

from readmodel.api.types import DefaultEntity

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
            default_entity: DefaultEntity = strawberry.field(
                resolver=self._default_entity_handler
            )

        return Schema(query=Query, enable_federation_2=True)

    def _status_handler(self) -> str:
        log.info("Received status request - responding OK.")
        return "OK"

    def _default_entity_handler(self) -> DefaultEntity:
        return DefaultEntity(
            id="c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
            type="PERSON",
            name="Johann Sebastian Bach",
        )
