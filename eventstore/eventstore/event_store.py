"""
Primary class of the EventStore component. Supports writing to the
canonical database for the History Atlas.
"""

import asyncio
import logging
import signal

from abstract_domain_model.transform import to_dict
from eventstore.database import Database
from eventstore.broker import Broker
from tha_config import Config

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class EventStore:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.broker = Broker(self.config, self.process_event)

    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f"Received shutdown signal: {signal}")
        await self.broker.cancel()

    async def process_event(self, event, pub_func):
        """accepts an event and submits it to the datastore for storage.
        Returns a json string representation of the persisted event."""
        log.debug(f"processing event {event}")
        persisted_events = self.db.commit_event(event)
        for event in persisted_events:
            await pub_func(to_dict(event))
        log.info("Finished processing event")


if __name__ == "__main__":
    store = EventStore()
    loop = asyncio.get_event_loop()
    loop.create_task(store.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(store.shutdown(s)))
    try:
        log.info("Asyncio loop now running")
        loop.run_forever()
    finally:
        loop.close()
        log.info("EventStore shut down successfully.")
