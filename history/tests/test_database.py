from datetime import datetime
import json
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from event_schema.EventSchema import Event
from history_service.database import Database
from testlib.seed.data.events import EVENTS


def test_get_all_events(db):
    gen = db.get_event_generator()
    c = 0
    for e in gen:
        c += 1
    assert c == len(EVENTS)


def test_get_events_from_halfway(db):
    gen = db.get_event_generator(3)
    c = 0
    for e in gen:
        c += 1
    assert c == len(EVENTS) // 2


def test_get_events_returns_dict(db):
    gen = db.get_event_generator(999)
    for e in gen:
        assert isinstance(e, dict)
        e["event_id"]
        e["type"]
        e["transaction_guid"]
        e["app_version"]
        e["timestamp"]
        e["user"]
        e["payload"]
        e["payload"]["use your imagination"]
