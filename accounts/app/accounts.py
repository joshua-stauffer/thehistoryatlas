"""
Core functionality for the Accounts Service.

October 16th, 2021
"""

import asyncio
import logging
import signal
from tha_config import Config

from app.broker import Broker
from app.database import Database
from app.query_handler import QueryHandler


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)

class Accounts:
    """Primary class for application. Primarily coordinates AMQP broker with
    database connection."""

    def __init__(self):
        self.config = Config()
        self.broker = None  # created asynchronously in ReadModel.start_broker()
        self.db = Database(self.config)
        self.qh = QueryHandler(self.db)

    def handle_query(self, msg):
        log.info(f"handling message {msg}")
        return self.qh.handle_query(msg)

    async def start_broker(self):
        """Initializes the message broker and starts listening for requests."""
        log.info('Accounts Service: starting broker')
        self.broker = Broker(
            self.config,
            self.handle_query,
        )
        try:
            await self.broker.start()
        except Exception as e:
            log.critical(f'Accounts Service caught unknown exception {e} and is ' + \
                          'shutting down without restart.')
            await self.shutdown()

    async def shutdown(self, signal=None):
        """Gracefully close all open connections and cancel tasks"""
        if signal:
            log.info(f'Received shutdown signal: {signal}')
        await self.broker.cancel()
        loop = asyncio.get_event_loop()
        tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
        log.info('Asyncio loop has been stopped')

if __name__ == '__main__':
    accounts = Accounts()
    log.info('Accounts initialized')
    loop = asyncio.get_event_loop()
    loop.create_task(accounts.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(accounts.shutdown(s)))
    try:
        log.info('Asyncio loop now running')
        loop.run_forever()
    finally:
        loop.close()
        log.info('Accounts shut down successfully.') 
