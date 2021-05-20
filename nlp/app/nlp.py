"""Primary point of entry for the natural language processing service of
the History Atlas.

May 13th, 2021
"""

import asyncio
from functools import partial
import logging
import os
import signal
from app.broker import Broker
from tha_config import Config
from app.state.database import Database
from app.processor import Processor
from app.resolver import Resolver
from app.trainer import Trainer


logging.basicConfig(level='DEBUG')
log = logging.getLogger(__name__)


class NLPService:

    def __init__(self):
        self.config = Config()
        self.config.TRAIN_DIR = '/app/train'    # directory for database to find training data
        self.config.OUT_DIR = '/app/models'     # directory for processor to find spaCy model
        self.config.DB_URI = 'sqlite+pysqlite:///:memory:'   # for now always use in memory db
        # setup communication with the rest of teh application
        self.broker = Broker(
            self.config,
            self.process_query,                 # single point of entry to NLP services
            self.process_response,              # Subqueries made while resolving a request
                                                #   will return here.
            self.train,                         # admin access to trigger model training
            self.process_event_stream,
            self.get_latest_event_id)
        self.db = Database(self.config)
        # request a replay of history

        # check for model, and build if none is found
        self.ensure_model()                     
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

    # history methods

    def process_event_stream(self, message):
        """Callback which handles events published to the emitted events stream."""
        self.db.handle_event(message)

    def get_latest_event_id(self):
        """Returns the last event processed by the database"""
        # Util method for the broker to know where we are in the replay
        return self.db.last_event_id

    # spaCy model management

    def ensure_model(self):
        """Checks that a model is available for the spaCy service, and builds
        one in case it is missing."""
        if not any(file.name == 'model-best' for file in os.scandir('/app/models')):
            log.info('No models were found. Building one now.')
            self.train()

    def train(self):
        """Builds a new training file based on the latest data, and then 
        trains a series of new models."""

        log.info('Starting model training. This could take a little while..')
        trainer = Trainer(self.config, self.db)
        trainer.build_training_file()
        log.info('Built training file. Now training model.')
        trainer.train()
        log.info('Finished training model, loading it now.')
        self.processor = Processor(load_model=True)



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
