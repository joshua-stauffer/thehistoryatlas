from datetime import datetime
import json
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from data import EVENTS
from event_schema.EventSchema import Event
from history_service.broker import Broker
from history_service.history import HistoryPlayer
from tha_config import Config


@pytest.fixture
def mock_send_tuple():
    queue = list()

    async def send_func(message):
        queue.append(message)

    def close_func():
        return

    return send_func, close_func, queue


@pytest.fixture
def history(db):
    with patch("history_service.history.Database"):
        with patch("history_service.history.Broker"):
            hp = HistoryPlayer()
            hp.db = db
            hp.broker = MagicMock(spec=Broker)
            return hp


def test_parse_msg_returns_zero_without_last_event_id(history):
    res = history._parse_msg({})
    assert res == 0


def test_parse_msg_with_arbitrary_value(history):
    res = history._parse_msg(
        {"type": "REQUEST_HISTORY_REPLAY", "payload": {"last_event_id": "not a number"}}
    )
    assert res == 0


def test_parse_msg_with_str(history):
    res = history._parse_msg({"payload": {"last_event_id": "4"}})
    assert isinstance(res, int)
    assert res == 4


def test_parse_msg_with_int(history):
    res = history._parse_msg({"last_event_id": 2})


@pytest.mark.asyncio
async def test_handle_request(history, mock_send_tuple):
    send_func, close_func, queue = mock_send_tuple
    await history.handle_request(
        {"type": "REQUEST_HISTORY_REPLAY", "payload": {"last_event_id": 0}},
        send_func,
        close_func,
    )
    assert len(queue) == len(EVENTS) + 1
    assert queue[-1]["type"] == "HISTORY_REPLAY_END"
    msg_id = 1
    for msg in queue[:-1]:
        assert msg["index"] == msg_id
        msg_id += 1


@pytest.mark.asyncio
async def test_handle_request_from_halfway(history, mock_send_tuple):
    send_func, close_func, queue = mock_send_tuple
    await history.handle_request(
        {"type": "REQUEST_HISTORY_REPLAY", "payload": {"last_event_id": 3}},
        send_func,
        close_func,
    )
    assert len(queue) == 4
    assert queue[-1]["type"] == "HISTORY_REPLAY_END"
