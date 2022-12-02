import asyncio
import signal
from logging import getLogger

from sanic import Sanic
from strawberry.sanic.views import GraphQLView

from writemodel.api.schema import get_schema
from writemodel.write_model import WriteModel


log = getLogger(__name__)


def run():
    writemodel = WriteModel()
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(writemodel.shutdown(s))
        )

    server = Sanic(__name__)
    schema = get_schema(app=writemodel)
    server.add_route(
        GraphQLView.as_view(schema=schema, graphiql=True),
        "/",
    )
    server.add_task(task=writemodel.start_broker())
    server.run(
        host=writemodel.config.SERVER_HOST,
        port=writemodel.config.SERVER_PORT
    )


if __name__ == "__main__":
    run()
