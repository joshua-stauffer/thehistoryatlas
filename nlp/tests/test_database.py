import os
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state.database import Database
from app.state.schema import AnnotatedCitation
from app.state.schema import Entity

ENTITIES = set(["PERSON", "PLACE", "TIME"])


class Config:
    """minimal class for setting up an in memory db for this test"""

    def __init__(self):
        self.DB_URI = "sqlite+pysqlite:///:memory:"
        self.DEBUG = False  # outputs all activity


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
