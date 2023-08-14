import asyncio
import signal
from logging import getLogger

from sanic import Sanic
from strawberry.sanic.views import GraphQLView

from the_history_atlas.apps.writemodel.write_model import WriteModelApp

log = getLogger(__name__)


def run():
    log.info("Initializing WriteModel")
    writemodel = WriteModelApp()
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(writemodel.shutdown(s))
        )

    server = Sanic(__name__)
    server.add_route(
        GraphQLView.as_view(schema=writemodel.api.get_schema(), graphiql=True),
        "/",
    )
    log.info("Starting WriteModel broker.")
    server.add_task(task=writemodel.init_services())
    HOST = writemodel._config_app.SERVER_HOST
    PORT = int(writemodel._config_app.SERVER_PORT)
    log.info(f"Starting Sanic server at {HOST}:{PORT}.")
    server.run(host=HOST, port=PORT, single_process=True)


if __name__ == "__main__":
    run()
