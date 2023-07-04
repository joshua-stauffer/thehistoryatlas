import json
import os
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from tests import TEST_ROOT_DIR
from the_history_atlas.apps.nlp.state.database import Database
from the_history_atlas.apps.nlp.state.schema import Base, AnnotatedCitation, Entity


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def db(config, engine):
    TEST_DB_URI = os.environ.get("TEST_DB_URI", None)

    if not TEST_DB_URI:
        raise Exception("Env variable `TEST_DB_URI` must be set to run test suite.")

    TRAIN_DIR = f"{TEST_ROOT_DIR}/test_apps/nlp/test_train_dir"

    db = Database(client=engine)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    fill_db(engine, TRAIN_DIR)

    return db


def fill_db(engine: Engine, training_dir: str):
    """Loads database with files found in base_training_data"""
    training_data = list()
    for file in os.scandir(training_dir):
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

    with Session(engine, future=True) as session:
        session.add_all(to_commit)
        session.commit()
