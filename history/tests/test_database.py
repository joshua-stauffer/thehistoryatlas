from datetime import datetime
import json
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from abstract_domain_model.types import Event
from event_schema.EventSchema import Event as EventModel
from history_service.database import Database
from seed import EVENTS


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
    gen = db.get_event_generator(4)
    for e in gen:
        assert isinstance(e, Event)
