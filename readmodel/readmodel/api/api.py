from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable, List

from readmodel.api.types import DefaultEntity, Source
from abstract_domain_model.models.readmodel import (
    DefaultEntity as DefaultEntityDomainObject,
    Source as SourceDomainObject,
)

log = getLogger(__name__)
log.setLevel("DEBUG")


class GQLApi:
    def __init__(
        self,
        default_entity_handler: Callable[[], DefaultEntityDomainObject],
        search_sources_handler: Callable[[str], List[SourceDomainObject]],
    ):
        self._default_entity_handler = default_entity_handler
        self._search_sources_handler = search_sources_handler

    def get_schema(self) -> Schema:
        """Output a GraphQL Schema."""

        @strawberry.type
        class Query:
            status: str = strawberry.field(resolver=self._status_handler)
            default_entity: DefaultEntity = strawberry.field(
                resolver=self._default_entity_resolver
            )
            search_sources: List[Source] = strawberry.field(
                resolver=self._search_sources_resolver
            )

        return Schema(query=Query, enable_federation_2=True)

    def _status_handler(self) -> str:
        log.info("Received status request - responding OK.")
        return "OK"

    def _default_entity_resolver(self) -> DefaultEntity:
        entity = self._default_entity_handler()
        log.info(f"Resolving default entity {entity.id}")
        return DefaultEntity(
            id=entity.id,
            type=entity.type,
            name=entity.name,
        )

    def _search_sources_resolver(self, search_term: str) -> List[Source]:
        log.info(f"Resolving source search for term {search_term}")
        sources = self._search_sources_handler(search_term)
        return sources
