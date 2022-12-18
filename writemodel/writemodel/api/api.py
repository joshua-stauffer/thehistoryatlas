from dataclasses import asdict
from logging import getLogger

import strawberry
from strawberry.federation import Schema
from typing import Callable, Literal

from abstract_domain_model.models import PublishCitation, PublishCitationPayload
from abstract_domain_model.models.commands import (
    CommandResponse,
    CommandSuccess,
    CommandFailed,
    Command,
    Entity,
    Person,
    Place,
    Time,
    Meta,
)
from writemodel.api.types import (
    AnnotateCitationInput,
    PublishCitationResponse,
    TagInput,
    EntityType,
)
from writemodel.utils import get_timestamp

log = getLogger(__name__)
log.setLevel("DEBUG")


class GQLApi:
    def __init__(
        self,
        command_handler: Callable[[Command], CommandResponse],
        auth_handler: Callable[[str], str],
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

                user_id = self._auth_handler(Annotation.token)

                publish_citation = self._transform_publish_citation(
                    data=Annotation, user_id=user_id
                )

                response = await self._command_handler(publish_citation)

                if isinstance(response, CommandSuccess):
                    return PublishCitationResponse(success=True, message=None)
                elif isinstance(response, CommandFailed):
                    return PublishCitationResponse(
                        success=False, reason=response.payload.reason
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
            app_version="0.0.1",
            payload=PublishCitationPayload(
                id=data.citation_guid,
                text=data.citation,
                summary=data.summary,
                summary_id=data.summary_guid,
                tags=[cls._transform_tag(tag) for tag in data.summary_tags],
                meta=Meta(
                    id=data.meta.GUID,
                    author=data.meta.author,
                    publisher=data.meta.publisher,
                    title=data.meta.title,
                    kwargs={
                        k: v
                        for k, v in asdict(data.meta).items()
                        if k in {"pageNum", "pubDate"}
                    },
                ),
            ),
        )
        return citation

    @classmethod
    def _transform_tag(cls, tag: TagInput) -> Entity:
        if tag.type == EntityType.PERSON:
            return Person(
                id=tag.GUID,
                type="PERSON",
                start_char=tag.start_char,
                stop_char=tag.stop_char,
                name=tag.name,
            )
        elif tag.type == EntityType.PLACE:
            return Place(
                id=tag.GUID,
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
                id=tag.GUID,
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
