"""
Primary class of the History component.

Provides read-only access to the canonical Event database,
for rebuilding or replaying history.
"""

import asyncio
import logging
import signal
import random
from typing import Optional

from abstract_domain_model.transform import to_dict
from history_service.database import Database
from history_service.broker import Broker
from tha_config import Config

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class HistoryPlayer:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.broker = Broker(self.config, self.handle_request)

    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f"Received shutdown signal: {signal}")
        await self.broker.cancel()

    def handle_request(
        self, request: dict, send_func, close_func
    ) -> Optional[asyncio.Task]:
        """callback method for broker.

        Parses request for parameters then passes events to
        send_func in batches.
        """
        msg_type = request.get("type")
        if not msg_type or msg_type != "REQUEST_HISTORY_REPLAY":
            log.info(
                "Received a malformed replay request. Discarding and doing nothing."
            )
            return None
        last_event_id = self._parse_msg(request)
        event_gen = self.db.get_event_generator(last_event_id)
        # move the generator operation off to another coroutine and return
        # a reference to it for easy cancellation if something goes wrong.
        task = asyncio.create_task(self._run_replay(event_gen, send_func, close_func))
        return task

    async def _run_replay(self, gen, send_func, close_func):
        """Manages the generator from a coroutine."""

        for event in gen:
            # adding a sleep in this coroutine helps to balance out requests
            # when multiple services are simultaneously requesting replays.
            if random.random() < 0.01:
                await asyncio.sleep(0.001)
                # add a bit of chaos -- randomly fail
                # log.info(f'Randomly killing this request on event {event.get("event_id")}!')
                # return close_func()
            await send_func(to_dict(event))
        # inform recipient that the stream is over
        await send_func({"type": "HISTORY_REPLAY_END", "payload": {}})
        # inform broker that the stream is over
        close_func()

    def _parse_msg(self, msg: dict):
        """Utility function to get correct values from request.

        Expects the following values in the message (and provides
        default values in case they aren't there):
            last_event_id: int

        Returns last_event_id
        """
        # figure out the event id, if any
        payload = msg.get("payload")
        if isinstance(payload, dict):
            last_event_id = payload.get("last_event_id", 0)
            if last_event_id:
                try:
                    last_event_id = int(last_event_id)
                except ValueError:
                    last_event_id = 0
        else:
            last_event_id = 0
        return last_event_id


if __name__ == "__main__":
    store = HistoryPlayer()
    log.info("History Player initialized")
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
        log.info("History Player shut down successfully.")
