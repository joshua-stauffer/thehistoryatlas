"""Read/Write access to the History Atlas query database.

May 3rd, 2021
"""

import asyncio
import logging
import signal
from typing import Dict

from abstract_domain_model.models.readmodel import DefaultEntity
from abstract_domain_model.transform import from_dict
from readmodel.api import GQLApi
from readmodel.broker import Broker
from tha_config import Config
from readmodel.state_manager.manager import Manager


logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class ReadModel:
    """Primary class for application. Primarily coordinates AMQP broker with
    database connection."""

    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.handle_query = self.manager.query_handler.handle_query
        self.broker = None  # created asynchronously in ReadModel.start_broker()
        self.api = GQLApi(default_entity_handler=self.default_entity_handler)

    def handle_event(self, event: Dict):
        event = from_dict(event)
        self.manager.event_handler.handle_event(event=event)

    def default_entity_handler(self) -> DefaultEntity:
        return self.manager.db.get_default_entity()

    async def start_broker(self):
        """Initializes the message broker and starts listening for requests."""
        log.info("ReadModel: starting broker")
        self.broker = Broker(
            self.config,
            self.handle_query,
            self.handle_event,
            self.manager.db.check_database_init,
        )
        last_event_id = self.manager.db.check_database_init()
        log.info(f"Last event id was {last_event_id}")
        try:
            # always replay history on restart to ensure data consistency
            await self.broker.start(is_initialized=False, replay_from=last_event_id)
        except Exception as e:
            log.critical(
                f"ReadModel caught unknown exception {e} and is "
                + "shutting down without restart."
            )
            await self.shutdown()

    async def init_services(self):
        """
        Start up any asynchronous services required by the application.
        """
        await self.start_broker()

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
