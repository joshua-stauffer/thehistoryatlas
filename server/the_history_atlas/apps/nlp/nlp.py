from functools import partial
import logging
import os
from shutil import copytree
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.nlp.state.database import Database
from the_history_atlas.apps.nlp.processor import Processor
from the_history_atlas.apps.nlp.resolver import Resolver
from the_history_atlas.apps.nlp.trainer import Trainer
from the_history_atlas.apps.domain.transform import from_dict


logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)

BASE_MODEL_DIR = "/app/base-models"
MODEL_DIR = "/app/models"
TRAIN_DIR = "/app/train"


class NLPService:
    def __init__(self):
        self.config = Config()
        self.config.TRAIN_DIR = (
            TRAIN_DIR  # directory for database to find training data
        )
        self.config.OUT_DIR = MODEL_DIR  # directory for processor to find spaCy model
        self.db = Database(self.config)
        # request a replay of history

        # check for model, and build if none is found
        self.ensure_model()
        self.processor = Processor(load_model=True)
        self.resolver_factory = partial(
            Resolver,
            query_geo=self.broker.query_geo,
            query_readmodel=self.broker.query_readmodel,
        )
        self._resolver_store = dict()

    async def process_query(self, event, corr_id, pub_func):
        """Receives request for processing and fields a response."""
        text = event["payload"]["text"]
        log.debug(f"Processing text {text}")
        text_map, boundaries = self.processor.parse(text)
        log.debug(f"Resolving ReadModel and Geo queries.")
        resolver = self.resolver_factory(
            text=text,
            text_map=text_map,
            corr_id=corr_id,
            pub_func=pub_func,
            boundaries=boundaries,
        )
        self._resolver_store[corr_id] = resolver
        # open sub queries
        await resolver.open_queries()

    async def process_response(self, message, corr_id):
        """Handle subquery responses."""
        resolver = self._resolver_store.get(corr_id)
        if not resolver:
            return  # this reply came in too late, the query has already been rejected/resolved
        await resolver.handle_response(message)
        if resolver.has_resolved:
            del self._resolver_store[corr_id]

    # history methods

    def process_event_stream(self, message):
        """Callback which handles events published to the emitted events stream."""
        event = from_dict(message)
        self.db.handle_event(event)

    def get_latest_event_id(self):
        """Returns the last event processed by the database"""
        # Util method for the broker to know where we are in the replay
        return self.db.last_event_id

    # spaCy model management

    def ensure_model(self):
        """Checks that a model is available for the spaCy service, and builds
        one in case it is missing."""
        if not any(file.name == "model-best" for file in os.scandir(MODEL_DIR)):
            log.info("No models were found. Installing the base model now.")
            try:
                #
                log.debug("Looking for an existing model to copy")
                copytree(BASE_MODEL_DIR, MODEL_DIR, dirs_exist_ok=True)
            except OSError as e:
                log.debug(f"Caught exception {e}")
                log.info("Training spaCy model from scratch.")
                self.train()
            #
        else:
            log.info("Found existing model -- using model-best")

    def train(self):
        """Builds a new training file based on the latest data, and then
        trains a series of new models."""

        log.info("Starting model training. This could take a little while..")
        trainer = Trainer(self.config, self.db)
        trainer.build_training_file()
        log.info("Built training file, ready to train model.")
        trainer.train()
        log.info("Loading newly trained NLP model now.")
        self.processor = Processor(load_model=True)
