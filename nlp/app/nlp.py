"""Primary point of entry for the natural language processing service of
the History Atlas.

May 13th, 2021
"""

import asyncio
import logging
from nlp.tests.test_resolver import query_readmodel
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
        self.broker = Broker(self.config, self.process_query)
        self.processor = Processor(load_model=False)
        self.resolver = Resolver(
            query_geo=self.broker.query_geo,
            query_readmodel=self.broker.query_readmodel)

    async def start_broker(self):
        await self.broker.start()

    async def shutdown(self, signal):
        if signal:
            log.info(f'Received shutdown signal: {signal}')
        await self.broker.cancel()

    async def process_query(self, event):
        """Receives request for processing and fields a response"""
        text = event['payload']['text']
        log.debug(f'Processing text {text}')
        entities = self.processor.parse(text)
        log.debug(f'Parsed entities: {entities}')
        res = await self.resolver.query(entities)
        log.debug(f'Resolved entities: {res}')
        return {
            'type': 'TEXT_PROCESSED',
            'payload': { 'result': res }
        }


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
