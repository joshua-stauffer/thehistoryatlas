"""Read/Write access to the History Atlas query database.

May 3rd, 2021
"""

import asyncio
import os
import json
import logging
import signal
from broker import Broker
from tha_config import Config
from state_manager.manager import Manager


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)

class ReadModel:
    """Primary class for application. Primarily coordinates AMQP broker with
    database connection."""

    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.handle_query = self.manager.query_handler.handle_query
        self.handle_event = self.manager.event_handler.handle_event
        self.broker = None  # created asynchronously in ReadModel.start_broker()

    async def start_broker(self):
        """Initializes the message broker and starts listening for requests."""
        log.info('ReadModel: starting broker')
        self.broker = Broker(
            self.config,
            self.handle_query,
            self.handle_event
        )
        # TODO: add logic to check if database exists yet
        try:
            await self.broker.start(is_initialized=True)
        except Exception as e:
            log.critical(f'ReadModel caught unknown exception {e} and is shutting down without restart.')
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
    rm = ReadModel()
    log.info('ReadModel initialized')
    loop = asyncio.get_event_loop()
    loop.create_task(rm.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(rm.shutdown(s)))
    try:
        log.info('Asyncio loop now running')
        loop.run_forever()
    finally:
        loop.close()
        log.info('ReadModel shut down successfully.') 
