from fastapi import FastAPI, Depends

from the_history_atlas.api import mount_api
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.config import Config


def get_app() -> FastAPI:
    config_app = Config()
    app_manager = AppManager(config_app=config_app)

    def apps():
        return app_manager

    app = FastAPI(dependencies=[Depends(apps)])

    mount_api(app=app)
    return app


app = get_app()
