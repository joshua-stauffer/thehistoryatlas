from functools import partial

from ariadne.asgi import GraphQL
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from the_history_atlas.api.context import get_context
from the_history_atlas.api.rest import register_rest_endpoints
from the_history_atlas.api.schema import build_schema
from the_history_atlas.apps.app_manager import AppManager


def mount_api(app: FastAPI, app_manager: AppManager) -> FastAPI:
    app = register_rest_endpoints(app)
    schema = build_schema()
    get_context_value = partial(get_context, _apps=app_manager)
    graphql = GraphQL(schema, debug=True, context_value=get_context_value)
    app.mount("/graphql/", graphql)
    origins = ["http://localhost:3000", "https://the-history-atlas-server-4ubzi.ondigitalocean.app"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
