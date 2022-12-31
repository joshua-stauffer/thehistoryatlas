from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable

from readmodel.api.types import DefaultEntity

log = getLogger(__name__)
log.setLevel("DEBUG")


class GQLApi:
    def __init__(self, default_entity_handler: Callable[[], DefaultEntity]):
        self._default_entity_handler = default_entity_handler

    def get_schema(self) -> Schema:
        """Output a GraphQL Schema."""

        @strawberry.type
        class Query:
            status: str = strawberry.field(resolver=self._status_handler)
            default_entity: DefaultEntity = strawberry.field(
                resolver=self._default_entity_resolver
            )

        return Schema(query=Query, enable_federation_2=True)

    def _status_handler(self) -> str:
        log.info("Received status request - responding OK.")
        return "OK"

    def _default_entity_resolver(self) -> DefaultEntity:
        entity = self._default_entity_handler()
        return DefaultEntity(
            id=entity.id,
            type=entity.type,
            name=entity.name,
        )
