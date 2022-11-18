from asyncio import AbstractEventLoop

import strawberry
from sanic import Sanic
from strawberry import Schema
from strawberry.sanic.views import GraphQLView


from tha_config import Config
from writemodel.api.types import Query, Mutation


class WriteModelAPI:
    def __init__(self, schema: Schema) -> None:
        schema = strawberry.Schema(query=Query, mutation=Mutation)
        app = Sanic(__name__)
        app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=True),
            "/",
        )

    def run(self, host: str, port: int, loop: AbstractEventLoop):
        ...
