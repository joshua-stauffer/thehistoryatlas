from fastapi import FastAPI

from the_history_atlas.api import mount_api
from the_history_atlas.apps.app_manager import AppManager


def get_app() -> FastAPI:
    app = FastAPI()
    app_manager = AppManager()
    mount_api(app=app, app_manager=app_manager)
    return app
