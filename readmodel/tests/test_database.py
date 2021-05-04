import asyncio
import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state_manager.database import Database
from app.state_manager.schema import Citation, TagInstance, Time, Person, Place


class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = True

@pytest.fixture
def db():
    c = Config()
    # stm timeout is an asyncio.sleep value: by setting it to 0 we defer control
    # back to the main thread but return to it as soon as possible.
    return Database(c, stm_timeout=0)

@pytest.fixture
def citation_data_1():
    guid = str(uuid4())
    text = 'A sample text to test'
    return guid, text

@pytest.fixture
def citation_data_2():
    guid = str(uuid4())
    text = 'Some further sample text to test'
    return guid, text

@pytest.fixture
def transaction_guid():
    return uuid4()

def test_database_exists(db):
    assert db != None

@pytest.mark.asyncio
async def test_create_citation(db, citation_data_1, transaction_guid):
    citation_guid, text = citation_data_1
    assert len(db._Database__short_term_memory.keys()) == 0
    db.create_citation(
        transaction_guid=transaction_guid,
        citation_guid=citation_guid,
        text=text)
    assert len(db._Database__short_term_memory.keys()) == 1
    # get the id from short term memory
    stm_vals = db._Database__short_term_memory.values()
    for val in stm_vals:
        citation_id = val
        break
    assert val != None
    # double check that citation has made it into the database
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
            select(Citation).where(Citation.id == citation_id)
        ).scalar_one()
        assert res.text == text
        assert res.guid == citation_guid

    # check that short term memory is cleared
    await asyncio.sleep(0.000001)
    assert len(db._Database__short_term_memory.keys()) == 0
