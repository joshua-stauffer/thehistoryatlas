import os
import pytest
from app.trainer import Trainer

@pytest.fixture
def outdir(tmp_path):
    return str(tmp_path)

@pytest.fixture
def config(outdir):
    class Config:
        def __init__(self):
            self.TRAIN_DIR = outdir
    return Config()

@pytest.fixture
def db():
    class DB:
        def get_training_corpus(self):
            return [
                ('Here is a sample text with a name', [(1, 5, 'PERSON')]),
                ('Here is a sample text with a place', [(1, 5, 'PLACE')]),
                ('Here is a sample text with a time', [(1, 5, 'TIME')])
            ]
    return DB()
 

@pytest.fixture
def trainer(db, config):
    return Trainer(config=config, db=db)

def test_trainer_exists(trainer):
    assert trainer != None

def test_trainer_creates_something(trainer, outdir):
    # check the temp directory and ensure that it's empty
    start_out = os.scandir(outdir)
    files = [f.path for f in start_out]
    assert len(files) == 0
    # this method should create a new training file and place it in the temp directory
    trainer.build_training_file()
    # check the temp directory and ensure that it contains our training file
    end_out = os.scandir(outdir)
    files = [f.path for f in end_out]
    assert len(files) == 1
    assert files[0].endswith('train.spacy')
