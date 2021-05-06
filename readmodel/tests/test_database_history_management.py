import asyncio
import json
import logging
import pytest
import random
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.state_manager.database import Database
from app.state_manager.schema import History

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False

@pytest.fixture
def db():
    c = Config()
    # stm timeout is an asyncio.sleep value: by setting it to 0 we defer control
    # back to the main thread but return to it as soon as possible.
    return Database(c, stm_timeout=0)

def test_database_init(db):
    res = db.check_database_init()
    assert res == 0

def test_update_last_event_id(db):
    db.check_database_init()
    db.update_last_event_id(11)
    res = db.check_database_init()
    assert res == 11
