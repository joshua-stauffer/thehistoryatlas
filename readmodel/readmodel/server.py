import asyncio
import signal
from logging import getLogger

from sanic import Sanic
from strawberry.sanic.views import GraphQLView

from readmodel.read_model import ReadModel

log = getLogger(__name__)


def run():
    readmodel = ReadModel()
    log.info("ReadModel initialized")
    loop = asyncio.get_event_loop()
    loop.create_task(readmodel.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(readmodel.shutdown(s))
        )

    server = Sanic(__name__)
    server.add_route(
        GraphQLView.as_view(schema=readmodel.api.get_schema(), graphiql=True),
        "/",
    )
    log.info("Starting ReadModel broker.")
    server.add_task(task=readmodel.init_services())
    HOST = readmodel.config.SERVER_HOST
    PORT = int(readmodel.config.SERVER_PORT)
    log.info(f"Starting Sanic server at {HOST}:{PORT}.")
    server.run(host=HOST, port=PORT, single_process=True)


if __name__ == "__main__":
    run()
