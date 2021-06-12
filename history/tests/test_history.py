from datetime import datetime
import json
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from event_schema.EventSchema import Event
from app.history import HistoryPlayer
from tha_config import Config


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

class MockConfig(Config):
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        super().__init__()
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False # outputs all activity

@pytest.fixture
def empty_history(mocker):
    # Mock the HistoryConfig object in the location it's being called from,
    # i.e. in the history module, not in the history_config module.
    mocker.patch('app.history.HistoryConfig', new=MockConfig)
    return HistoryPlayer()

@pytest.fixture
def history(empty_history, event):
    db = empty_history.db
    for _ in range(1000):
        e = Event(**event)
        with Session(db._engine, future=True) as sess, sess.begin():
            sess.add(e)
    return empty_history

@pytest.fixture
def mock_send_tuple():
    queue = list()
    async def send_func(message):
        queue.append(message)
    def close_func():
        return
    return send_func, close_func, queue

def test_history_exists(empty_history):
    assert empty_history != None

def test_history_with_events(history):
    assert history != None

def test_parse_msg_returns_zero_without_last_event_id(history):
    res = history._parse_msg({})
    assert res == 0

def test_parse_msg_with_arbitrary_value(history):
    res = history._parse_msg({
        'type': 'REQUEST_HISTORY_REPLAY',
        'payload': {'last_event_id': 'not a number'}
    })
    assert res == 0

def test_parse_msg_with_str(history):
    res = history._parse_msg({
        'payload': {'last_event_id': '11'}
    })
    assert isinstance(res, int)
    assert res == 11

def test_parse_msg_with_int(history):
    res = history._parse_msg({
        'last_event_id': 27
    })

@pytest.mark.asyncio
async def test_handle_request(history, mock_send_tuple):
    send_func, close_func, queue = mock_send_tuple
    await history.handle_request({
        'type': 'REQUEST_HISTORY_REPLAY',
        'payload': {
            'last_event_id': 0
        }
    }, send_func, close_func)
    assert len(queue) == 1001
    assert queue[-1]['type'] == 'HISTORY_REPLAY_END'
    msg_id = 1
    for msg in queue[:-1]:
        assert msg['event_id'] == msg_id
        msg_id += 1
    
@pytest.mark.asyncio
async def test_handle_request_from_halfway(history, mock_send_tuple):
    send_func, close_func, queue = mock_send_tuple
    await history.handle_request({
        'type': 'REQUEST_HISTORY_REPLAY',
        'payload': {
            'last_event_id': 500
        }
    }, send_func, close_func)
    assert len(queue) == 501
    assert queue[-1]['type'] == 'HISTORY_REPLAY_END'
    
