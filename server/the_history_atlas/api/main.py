from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from the_history_atlas.api.rest import register_rest_endpoints
from the_history_atlas.apps.app_manager import AppManager


def mount_api(fastapi_app: FastAPI, apps: Callable[[], AppManager]) -> FastAPI:
    app = register_rest_endpoints(fastapi_app=fastapi_app, app_manager=apps)
    origins = [
        "http://localhost:3000",
        "https://historyatlas.org",
        "https://www.historyatlas.org",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
