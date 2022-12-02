from typing import Literal

import strawberry

# from strawberry.federation import Schema
from strawberry import Schema


from writemodel.api.types import AnnotateCitationInput
from writemodel.write_model import WriteModel


def get_schema(app: WriteModel) -> Schema:
    @strawberry.type
    class Query:
        ...

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def PublishNewCitation(
            self, Annotation: AnnotateCitationInput
        ) -> Literal[str, str, bool]:
            return "test", "test", True

    return strawberry.Schema(query=Query, mutation=Mutation)
