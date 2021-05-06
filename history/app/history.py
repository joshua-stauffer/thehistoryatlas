"""
Primary class of the History component.

Provides read-only access to the canonical Event database,
for rebuilding or replaying history.
"""

import asyncio
import json
import logging
import os
import signal
from .database import Database
from broker import Broker
from history_config import HistoryConfig

logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)

class HistoryPlayer:

    def __init__(self):
        self.config = HistoryConfig()
        self.db = Database(self.config)
        self.broker = Broker(self.config, self.handle_request)

    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f'Received shutdown signal: {signal}')
        await self.broker.cancel()

    async def handle_request(self, request: dict, send_func):
        """callback method for broker. 
        
        Parses request for parameters then passes events to
        send_func in batches.
        """
        msg_type = request.get('type')
        if not msg_type or msg_type != 'REQUEST_HISTORY_REPLAY':
            log.info('Received a malformed replay request. Discarding and doing nothing.')
            return
        last_event_id = self._parse_msg(request)
        event_gen = self.db.get_event_generator(last_event_id)

        for event in event_gen:
            await send_func(event)
        await send_func({
            'type': 'HISTORY_REPLAY_END',
            'payload': {}
        })

    def _parse_msg(self, msg: dict):
        """Utility function to get correct values from request.
        
        Expects the following values in the message (and provides
        default values in case they aren't there):
            last_event_id: int

        Returns last_event_id
        """
        # figure out the event id, if any
        payload = msg.get('payload')
        if isinstance(payload, dict):
            last_event_id = payload.get('last_event_id', 0)
            if last_event_id:
                try:
                    last_event_id = int(last_event_id)
                except ValueError:
                    last_event_id = 0
        else:
            last_event_id = 0
        return last_event_id


if __name__ == '__main__':
    store = HistoryPlayer()
    log.info('History Player initialized')
    loop = asyncio.get_event_loop()
    loop.create_task(store.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(store.shutdown(s)))
    try:
        log.info('Asyncio loop now running')
        loop.run_forever()
    finally:
        loop.close()
        log.info('History Player shut down successfully.') 
