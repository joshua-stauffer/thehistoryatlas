"""SQLAlchemy integration for the History Atlas NLP service.
Stores annotations for training model.
"""
from collections import namedtuple
import logging
import json
import os
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state.schema import AnnotatedCitation
from app.state.schema import Base
from app.state.schema import Entity
from app.state.schema import Init


log = logging.getLogger(__name__)

CitationEntry = namedtuple("AnnotatedCitation", ["text", "entities"])


class Database:
    def __init__(self, config):
        self._config = config
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.last_event_id = 0
        if self._db_is_empty():
            self._fill_db()

    def _db_is_empty(self) -> bool:
        """Checks to see if database is empty."""
        with Session(self._engine, future=True) as session:
            res = session.execute(select(Init).where(Init.id == 1)).scalar_one_or_none()
            if res == None:
                return True
            else:
                return False

    def _fill_db(self):
        """Loads database with files found in base_training_data"""
        log.info("Filling the DB with initial training data")
        training_data = list()
        for file in os.scandir(self._config.TRAIN_DIR):
            if os.path.isfile(file) and file.name.endswith(".json"):
                with open(file.path, "r") as f:
                    json_file = json.load(f)
                    for entry in json_file:
                        training_data.append(entry)
        to_commit = list()
        for citation in training_data:
            content = citation.get("content")
            entities = citation.get("entities")
            annotated_citation = AnnotatedCitation(text=content)
            to_commit.append(annotated_citation)
            entity_list = [
                Entity(
                    start_char=e[0],
                    stop_char=e[1],
                    type=e[2],
                    annotated_citation=annotated_citation,
                )
                for e in entities
            ]
            to_commit.extend(entity_list)

        init = Init(is_initialized=True)
        to_commit.append(init)
        log.info(f"Initializing DB with {len(to_commit)} objects")
        with Session(self._engine, future=True) as session:
            session.add_all(to_commit)
            session.commit()

    def get_training_corpus(self):
        """"""
        # might make sense to make this into a generator at some point
        res = list()
        with Session(self._engine, future=True) as session:
            citations = session.execute(select(AnnotatedCitation)).scalars()
            for citation in citations:
                text = citation.text
                entities = [
                    (e.start_char, e.stop_char, e.type) for e in citation.entities
                ]
                res.append(CitationEntry(text, entities))
        return res

    def handle_event(self, event):
        """Process an emitted event and save it to the database"""
        # this isn't as strict with messages being lost/out of order, but
        # shouldn't be a huge deal for this particular use case.
        id = event.get("event_id")
        if id > self.last_event_id:
            self.last_event_id = id
