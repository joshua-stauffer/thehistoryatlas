from fastapi import FastAPI

from the_history_atlas.api import mount_api
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.config import Config


def get_app() -> FastAPI:
    app = FastAPI()
    config_app = Config()
    app_manager = AppManager(config_app=config_app)
    mount_api(app=app, app_manager=app_manager)
    return app
