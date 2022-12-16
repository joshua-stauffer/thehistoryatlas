import strawberry
from strawberry.federation import Schema
from typing import Callable, Union

from abstract_domain_model.models import PublishCitation
from abstract_domain_model.models.commands import (
    CommandResponse,
    CommandSuccess,
    CommandFailed,
    Command,
)
from writemodel.api.types import AnnotateCitationInput, PublishCitationResponse
from writemodel.utils import get_timestamp


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
            status: str = strawberry.field(resolver=lambda: "ok")

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def PublishNewCitation(
                _, Annotation: AnnotateCitationInput
            ) -> PublishCitationResponse:

                user_id = self._auth_handler(Annotation.token)

                publish_citation = self.transform_publish_citation(
                    data=Annotation, user_id=user_id
                )

                response = self._command_handler(publish_citation)

                if isinstance(response, CommandSuccess):
                    return PublishCitationResponse(success=True, message=None)
                elif isinstance(response, CommandFailed):
                    return PublishCitationResponse(
                        success=False, reason=response.payload.reason
                    )
                else:
                    raise Exception("Unexpected error occurred.")

        return Schema(query=Query, mutation=Mutation, enable_federation_2=True)

    @staticmethod
    def transform_publish_citation(
        data: AnnotateCitationInput, user_id: str
    ) -> PublishCitation:
        """Transform GQL type to domain model type."""
        return PublishCitation(
            user_id=user_id,
            timestamp=get_timestamp(),
            app_version=app_version,
        )
