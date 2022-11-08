from copy import deepcopy

import pytest

from seed import EVENTS
from tha_config import get_from_env


@pytest.fixture(scope="session")
def event_emitted_broker(TestBroker):
    """Instantiate a broker to handle the EVENT_PERSISTED event."""
    # results will be available via broker.results
    listen_to_routing_key = get_from_env(
        variable="EVENTSTORE__EVENT_PERSISTED_ROUTING_KEY"
    )
    broker = TestBroker(queue_name="test_broker", listen_to=listen_to_routing_key)
    return broker


@pytest.fixture
def events():
    return [deepcopy(event) for event in EVENTS]


@pytest.fixture(scope="session")
def event_emitted_result(event_emitted_broker, run_integration_test, events):
    results = run_integration_test(
        broker=event_emitted_broker,
        messages=events,
        routing_key=get_from_env(variable="EVENTSTORE__EVENT_EMITTED_ROUTING_KEY"),
        expected_result_count=len(events)
    )
    return results


def test_eventstore_adds_indices(event_emitted_result):
    for i, event in enumerate(event_emitted_result):
        assert event.index == i


