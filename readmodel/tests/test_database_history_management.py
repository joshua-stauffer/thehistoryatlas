import asyncio
import json
import logging
import pytest
import random
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from readmodel.state_manager.database import Database
from readmodel.state_manager.schema import History


def test_database_init(db):
    res = db.check_database_init()
    assert res == 0


def test_update_last_event_id(db):
    db.check_database_init()
    db.update_last_event_id(11)
    res = db.check_database_init()
    assert res == 11
