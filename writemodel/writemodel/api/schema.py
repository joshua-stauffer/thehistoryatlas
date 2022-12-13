import strawberry

from strawberry.federation import Schema

from abstract_domain_model.models.commands import CommandSuccess, CommandFailed
from writemodel.api.types import AnnotateCitationInput, PublishCitationResponse
from writemodel.write_model import WriteModel


def get_schema(app: WriteModel) -> Schema:
    @strawberry.type
    class Query:
        status: str = strawberry.field(resolver=lambda: "ok")

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def PublishNewCitation(
            self, Annotation: AnnotateCitationInput
        ) -> PublishCitationResponse:
            response = app.handle_command(Annotation)
            if isinstance(response, CommandSuccess):
                return PublishCitationResponse(success=True, message=None)
            elif isinstance(response, CommandFailed):
                return PublishCitationResponse(
                    success=False, reason=response.payload.reason
                )
            else:
                raise Exception("Unexpected error occurred.")

    return Schema(query=Query, mutation=Mutation, enable_federation_2=True)
