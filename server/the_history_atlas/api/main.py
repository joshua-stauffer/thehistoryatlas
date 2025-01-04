from functools import partial

from ariadne.asgi import GraphQL
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from the_history_atlas.api.rest import register_rest_endpoints
from the_history_atlas.apps.app_manager import AppManager


def mount_api(app: FastAPI, app_manager: AppManager) -> FastAPI:
    app = register_rest_endpoints(app)
    origins = ["http://localhost:3000", "https://urchin-app-f6n6t.ondigitalocean.app"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
