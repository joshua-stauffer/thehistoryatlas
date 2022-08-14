import json
import os
from logging import getLogger
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from nlp_service.state.database import Database
from nlp_service.state.schema import AnnotatedCitation
from nlp_service.state.schema import Entity

log = getLogger(__name__)

ENTITIES = {"PERSON", "PLACE", "TIME"}


class Config:
    """minimal class for setting up an in memory db for this test"""

    def __init__(self):
        self.DB_URI = "postgresql+psycopg2://postgres:hardpass123@localhost:5432/nlp"
        self.DEBUG = False  # outputs all activity
        # TODO: make this dynamic
        self.TRAIN_DIR = (
            "/Users/josh/dev/thehistoryatlas/nlp/tests/test_train_dir/train.json"
        )


def fill_db(config: Config, engine: Engine):
    """Loads database with files found in base_training_data"""
    log.info("Filling the DB with initial training data")
    training_data = list()
    for file in os.scandir(config.TRAIN_DIR):
        if os.path.isfile(file) and file.name.endswith(".json"):
            with open(file.path, "r") as f:
                json_file = json.load(f)
                for entry in json_file:
                    training_data.append(entry)
    to_commit = list()
    for citation in training_data:
        citation_id = str(uuid4())
        content = citation.get("content")
        entities = citation.get("entities")
        annotated_citation = AnnotatedCitation(text=content, id=citation_id)
        to_commit.append(annotated_citation)
        entity_list = [
            Entity(
                id=str(uuid4()),
                start_char=e[0],
                stop_char=e[1],
                type=e[2],
                annotated_citation=annotated_citation,
            )
            for e in entities
        ]
        to_commit.extend(entity_list)

    to_commit.append(init)
    log.info(f"Initializing DB with {len(to_commit)} objects")
    with Session(self._engine, future=True) as session:
        session.add_all(to_commit)
        session.commit()


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def db(config):
    root = os.getcwd()
    config.TRAIN_DIR = root + "/tests/test_train_dir"
    config.debug = True
    db = Database(config)

    return db


def test_db_exists(db):
    assert db != None


def test_is_db_empty(db):
    assert db._db_is_empty() == False


def test_db_content(db):
    db._fill_db()
    with Session(db._engine, future=True) as session:
        annotated_citations = session.execute(select(AnnotatedCitation)).scalars()
        # there are results, right?
        assert len([r.id for r in annotated_citations]) > 0
        tags = session.execute(select(Entity)).scalars()
        # there are results, right?
        assert len([r.id for r in tags]) > 0


def test_get_training_corpus(db):
    res = db.get_training_corpus()
    assert res != None
    # replicate the standard access pattern
    for text, entities in res:
        assert isinstance(text, str)
        assert isinstance(entities, list)
        for start, stop, label in entities:
            assert isinstance(stop, int)
            assert isinstance(start, int)
            assert isinstance(label, str)
            assert label in ENTITIES
