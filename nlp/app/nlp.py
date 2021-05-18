"""Primary point of entry for the natural language processing service of
the History Atlas.

May 13th, 2021
"""

import asyncio
from functools import partial
import logging
import signal
from app.broker import Broker
from tha_config import Config
from app.processor import Processor
from app.resolver import Resolver


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)


class NLPService:

    def __init__(self):
        self.config = Config()
        self.broker = Broker(
            self.config,
            self.process_query,     # single point of entry to NLP services
            self.process_response)  # Subqueries made while resolving a request
                                    # will return here.
        self.processor = Processor(load_model=True)
        self.resolver_factory = partial(
            Resolver,
            query_geo=self.broker.query_geo,
            query_readmodel=self.broker.query_readmodel)
        self._resolver_store = dict()

    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f'Received shutdown signal: {signal}')
        await self.broker.cancel()

    async def process_query(self, event, corr_id, pub_func):
        """Receives request for processing and fields a response."""
        text = event['payload']['text']
        log.debug(f'Processing text {text}')
        text_map = self.processor.parse(text)
        log.debug(f'Resolving ReadModel and Geo queries.')
        resolver = self.resolver_factory(
            text=text,
            text_map=text_map,
            corr_id=corr_id,
            pub_func=pub_func)
        self._resolver_store[corr_id] = resolver
        # open sub queries
        await resolver.open_queries()

    async def process_response(self, message, corr_id):
        """Handle subquery responses."""
        resolver = self._resolver_store.get(corr_id)
        if not resolver:
            return # this reply came in too late, the query has already been rejected/resolved
        await resolver.handle_response(message)
        if resolver.has_resolved:
            del self._resolver_store[corr_id]


if __name__ == "__main__":
    log.info('Starting NLP Service')
    nlp = NLPService()
    loop = asyncio.get_event_loop()
    loop.create_task(nlp.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(nlp.shutdown(s)))
    try:
        log.info('Asyncio loop now running')
        loop.run_forever()
    finally:
        loop.close()
        log.info('NLPService shut down successfully.') 
