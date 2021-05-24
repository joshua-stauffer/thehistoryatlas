"""Primary point of entry for the GeoService application of the History Atlas.

This application listens to requests on the query.geo topic, and expects to be
given a series of names. It then tries to match those names with coordinates
in the database and returns the results.

May 21st, 2021"""

import asyncio
import logging
import signal
from tha_config import Config
from app.broker import Broker
from app.state.database import Database
from app.state.query_handler import QueryHandler


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)


class GeoService:

    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.query_handler =QueryHandler(self.db)
        self.broker = Broker(
            self.config,
            self.query_handler.handle_query)
   
    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f'Received shutdown signal: {signal}')
        await self.broker.cancel()


if __name__ == "__main__":
    log.info('Starting Geo Service')
    geo = GeoService()
    loop = asyncio.get_event_loop()
    loop.create_task(geo.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(geo.shutdown(s)))
    try:
        log.info('Asyncio loop now running')
        loop.run_forever()
    finally:
        loop.close()
        log.info('GeoService shut down successfully.') 
