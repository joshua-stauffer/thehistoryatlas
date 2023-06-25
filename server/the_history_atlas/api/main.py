from functools import partial

from ariadne.asgi import GraphQL
from fastapi import FastAPI

from the_history_atlas.api.context import get_context
from the_history_atlas.api.schema import build_schema
from the_history_atlas.apps.app_manager import AppManager


def mount_api(app: FastAPI, app_manager: AppManager) -> FastAPI:
    schema = build_schema()
    get_context_value = partial(get_context, _apps=app_manager)
    graphql = GraphQL(schema, debug=True, context_value=get_context_value)
    app.mount("/graphql/", graphql)
    return app
