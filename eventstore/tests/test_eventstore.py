from app.event_store import EventStore
from tha_config import Config
import pytest

class MockConfig(Config):
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        super().__init__()
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False # outputs all activity


def test_eventstore(mocker):
    mocker.patch('app.event_store.Config', new=MockConfig)
    store = EventStore()
    assert store != None
