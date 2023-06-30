from functools import partial
import logging
import os
from shutil import copytree
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.models import TextAnalysis, GetTextAnalysis
from the_history_atlas.apps.domain.models.nlp.text_analysis import TextAnalysisResponse
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.nlp.state.database import Database
from the_history_atlas.apps.nlp.processor import Processor
from the_history_atlas.apps.nlp.resolver import Resolver
from the_history_atlas.apps.nlp.trainer import Trainer
from the_history_atlas.apps.domain.transform import from_dict
from the_history_atlas.apps.readmodel import ReadModelApp

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)

BASE_MODEL_DIR = "/app/base-models"
MODEL_DIR = "/app/models"
TRAIN_DIR = "/app/train"


class NaturalLanguageProcessingApp:
    def __init__(
        self,
        database_client: DatabaseClient,
        config_app: Config,
        readmodel_app: ReadModelApp,
    ):
        self.config = config_app
        self._readmodel_app = readmodel_app
        self.config.TRAIN_DIR = (
            TRAIN_DIR  # directory for database to find training data
        )
        self.config.OUT_DIR = MODEL_DIR  # directory for processor to find spaCy model
        self.db = Database(client=database_client)

        # check for model, and build if none is found
        self.ensure_model()
        self.processor = Processor(load_model=True)

    def get_text_analysis(self, data: GetTextAnalysis) -> TextAnalysisResponse:
        """Receives request for processing and fields a response."""

        text_map, boundaries = self.processor.parse(data.text)
        resolver = Resolver(
            text=data.text,
            text_map=text_map,
            boundaries=boundaries,
            readmodel_app=self._readmodel_app,
        )
        text_analysis_result = resolver.run()
        return text_analysis_result

    def handle_event(self, event: Event):
        """Callback which handles events published to the emitted events stream."""
        self.db.handle_event(event)

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
