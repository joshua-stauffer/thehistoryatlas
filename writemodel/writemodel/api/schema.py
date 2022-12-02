from typing import Literal

import strawberry

from strawberry.federation import Schema


from writemodel.api.types import AnnotateCitationInput
from writemodel.write_model import WriteModel


def get_schema(app: WriteModel) -> Schema:
    @strawberry.type
    class Query:
        name: str = strawberry.field(resolver=lambda : "test")

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def PublishNewCitation(
            self, Annotation: AnnotateCitationInput
        ) -> str:
            return "test"

    return Schema(query=Query, mutation=Mutation, enable_federation_2=True)
