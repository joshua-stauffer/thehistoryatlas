from datetime import datetime
import json
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import Database
from event_schema.EventSchema import Event

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False # outputs all activity

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def db(config, event):
    db = Database(config)
    for _ in range(1000):
        e = Event(**event)
        with Session(db._engine, future=True) as sess, sess.begin():
            sess.add(e)
    return db

@pytest.fixture
def event():
    return {
        'type': 'TEST_EVENT',
        'transaction_guid': str(uuid4()),
        'app_version': '0.0.0',
        'user': str(uuid4()),
        'timestamp': str(datetime.utcnow()),
        'payload': json.dumps({
            'use your imagination': ', kid!'
        })
    }


def test_database_exists(db):
    assert db != None
    # check that it's empty
    with Session(db._engine, future=True) as sess:
        res = sess.execute(
                select(Event).where(Event.id == 1000)
            ).scalar_one_or_none()
        assert res != None

def test_get_all_events(db):
    gen = db.get_events()
    c = 0
    for e in gen:
        c += 1
    assert c == 1000

def test_get_events_from_halfway(db):
    gen = db.get_events(500)
    c = 0
    for e in gen:
        c += 1
    assert c == 500

def test_get_events_returns_json_string(db):
    gen = db.get_events(999)
    for e in gen:
        e = json.loads(e)
        e['id']
        e['type']
        e['transaction_guid']
        e['app_version']
        e['timestamp']
        e['user']
        e['payload']
        e['payload']['use your imagination']
