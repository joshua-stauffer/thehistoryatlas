"""Entry point for the WriteModel component.

Receives config variables from the environment via the Config module.
Integrates handler modules (command_handler and event_handler) and database
access via the Manager module.
Communicates with the rest of the History Atlas through the Broker module.
"""

import asyncio
import os
import json
import logging
import signal
from tha_config import Config
from writemodel.broker import Broker
from writemodel.state_manager.manager import Manager

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class WriteModel:
    """Primary class to serve the Write Event. Starts database connection on
    instantiation, and is available to broker after calling
    WriteModel.start_broker()"""

    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.handle_command = self.manager.command_handler.handle_command
        self.handle_event = self.manager.event_handler.handle_event
        self.broker = None  # created asynchronously in WriteModel.start_broker()

    async def start_broker(self):
        """Initializes the message broker and starts listening for requests."""
        log.info("WriteModel: starting broker")
        self.broker = Broker(
            self.config,
            self.handle_command,
            self.handle_event,
            self.manager.db.check_database_init,
        )
        last_event_id = self.manager.db.check_database_init()
        log.info(f"Last event id was {last_event_id}")

        try:
            await self.broker.start(is_initialized=False, replay_from=last_event_id)
        except Exception as e:
            log.critical(
                f"WriteModel caught unknown exception {e} and is "
                + "shutting down without restart."
            )
            await self.shutdown()

    async def shutdown(self, signal=None):
        """Gracefully close all open connections and cancel tasks"""
        if signal:
            log.info(f"Received shutdown signal: {signal}")
        await self.broker.cancel()
        loop = asyncio.get_event_loop()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
        log.info("Asyncio loop has been stopped")


if __name__ == "__main__":
    wm = WriteModel()
    log.info("WriteModel initialized")
    loop = asyncio.get_event_loop()
    loop.create_task(wm.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(wm.shutdown(s)))
    try:
        log.info("Asyncio loop now running")
        loop.run_forever()
    finally:
        loop.close()
        log.info("WriteModel shut down successfully.")
