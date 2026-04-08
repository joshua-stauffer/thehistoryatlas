import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from the_history_atlas.api import mount_api
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.config import Config


def get_app() -> FastAPI:
    config_app = Config()
    app_manager = AppManager(config_app=config_app)

    def apps():
        return app_manager

    fastapi_app = FastAPI()

    # Add Prometheus metrics instrumentation with default settings
    instrumentator = Instrumentator(
        excluded_handlers=[".*admin.*", "/metrics"],
    )
    instrumentator.instrument(fastapi_app).expose(fastapi_app, endpoint="/metrics")

    mount_api(
        fastapi_app=fastapi_app,
        apps=apps,
    )
    return fastapi_app


app = get_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
