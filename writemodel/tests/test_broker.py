import asyncio
from collections import deque
from collections.abc import Callable
from uuid import uuid4
import pytest
from writemodel.broker import Broker

@pytest.fixture
def broker(monkeypatch, get_latest_event_id, create_message_tuple, publish_one_tuple):
    # patch init to not inherit from BrokerBase
    def mock_init(self):
        return
    monkeypatch.setattr(Broker, '__init__', mock_init)
    b = Broker()
    # set init attributes by hand
    b.is_history_replaying = False
    b._history_queue = deque()
    b._HISTORY_TIMEOUT = 0
    b._history_timeout_coro = None
    b._history_replay_corr_id = None
    b._get_latest_event_id = get_latest_event_id
    # mock inherited methods which we need
    # store the results right on the object, taking care to not overwrite anything
    create_message, create_message_store = create_message_tuple
    b.create_message = create_message
    b.create_message_store = create_message_store
    publish_one, publish_one_store = publish_one_tuple
    b.publish_one = publish_one
    b.publish_one_store = publish_one_store
    return b

@pytest.fixture
def get_latest_event_id():
    def func():
        # lets always return 11
        return 11
    return func

@pytest.fixture
def create_message_tuple():
    store = list()
    def create_message(self, *args, **kwargs):
        store.append([args, kwargs])
    return create_message, store

@pytest.fixture
def publish_one_tuple():
    store = list()
    async def publish_one(self, *args, **kwargs):
        store.append([args, kwargs])
    return publish_one, store


def test_broker_exists(broker):
    assert broker != None

@pytest.mark.asyncio
async def test_request_history_replay_no_index(broker):
    await broker._request_history_replay()
    assert broker.is_history_replaying == True
    assert isinstance(broker._history_timeout_coro, asyncio.Task)
    assert len(broker.create_message_store) == 1
    await asyncio.sleep(0.00000001)
    assert broker.is_history_replaying == False
