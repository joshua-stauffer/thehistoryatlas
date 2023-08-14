from dataclasses import asdict
from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable, Awaitable

from the_history_atlas.apps.domain.models import PublishCitation, PublishCitationPayload
from the_history_atlas.apps.domain.models.commands import (
    CommandResponse,
    CommandSuccess,
    CommandFailed,
    Entity,
    Person,
    Place,
    Time,
    Meta,
)
from the_history_atlas.apps.domain.types import Command
from the_history_atlas.apps.writemodel.api.types import (
    AnnotateCitationInput,
    PublishCitationResponse,
    TagInput,
    EntityType,
)
from the_history_atlas.apps.writemodel.utils import get_timestamp, get_app_version

log = getLogger(__name__)
log.setLevel("DEBUG")


class GQLApi:
    def __init__(
        self,
        command_handler: Callable[[Command], Awaitable[CommandResponse]],
        auth_handler: Callable[[str], Awaitable[str]],
    ):
        self._command_handler = command_handler
        self._auth_handler = auth_handler

    def get_schema(self) -> Schema:
        """Output a GraphQL Schema."""

        @strawberry.type
        class Query:
            status: str = strawberry.field(resolver=self._status_handler)

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            async def PublishNewCitation(
                Annotation: AnnotateCitationInput,
            ) -> PublishCitationResponse:

                user_id = await self._auth_handler(Annotation.token)

                publish_citation = self._transform_publish_citation(
                    data=Annotation, user_id=user_id
                )

                response = await self._command_handler(publish_citation)

                if isinstance(response, CommandSuccess):
                    return PublishCitationResponse(
                        success=True, message=None, token=Annotation.token
                    )
                elif isinstance(response, CommandFailed):
                    return PublishCitationResponse(
                        success=False,
                        message=response.payload.reason,
                        token=Annotation.token,
                    )
                else:
                    raise Exception("Unexpected error occurred.")

        return Schema(query=Query, mutation=Mutation, enable_federation_2=True)

    @classmethod
    def _transform_publish_citation(
        cls, data: AnnotateCitationInput, user_id: str
    ) -> PublishCitation:
        """Transform GQL type to domain model type."""
        citation = PublishCitation(
            user_id=user_id,
            timestamp=get_timestamp(),
            app_version=get_app_version(),
            payload=PublishCitationPayload(
                id=data.citation_id,
                text=data.citation,
                summary=data.summary,
                summary_id=data.summary_id,
                tags=[cls._transform_tag(tag) for tag in data.summary_tags],
                meta=Meta(
                    id=data.meta.id,
                    author=data.meta.author,
                    publisher=data.meta.publisher,
                    title=data.meta.title,
                    kwargs={
                        k: v
                        for k, v in asdict(data.meta).items()
                        if k in {"pageNum", "pubDate", "accessDate"}
                    },
                ),
            ),
        )
        return citation

    @classmethod
    def _transform_tag(cls, tag: TagInput) -> Entity:
        if tag.type == EntityType.PERSON:
            return Person(
                id=tag.id,
                type="PERSON",
                start_char=tag.start_char,
                stop_char=tag.stop_char,
                name=tag.name,
            )
        elif tag.type == EntityType.PLACE:
            return Place(
                id=tag.id,
                type="PLACE",
                start_char=tag.start_char,
                stop_char=tag.stop_char,
                name=tag.name,
                latitude=tag.latitude,
                longitude=tag.longitude,
                geo_shape=tag.geoshape,
            )
        elif tag.type == EntityType.TIME:
            return Time(
                id=tag.id,
                type="TIME",
                start_char=tag.start_char,
                stop_char=tag.stop_char,
                name=tag.name,
            )
        else:
            raise Exception(f"Unknown tag type received: `{tag.type}`")

    def _status_handler(self) -> str:
        log.info("Received status request - responding OK.")
        return "OK"
