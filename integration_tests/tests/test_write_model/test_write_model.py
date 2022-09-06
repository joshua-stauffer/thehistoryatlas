import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
from uuid import UUID

import pytest

from abstract_domain_model.transform import from_dict
from pybroker import BrokerBase
from seed import PUBLISH_CITATIONS, SYNTHETIC_EVENTS, ADD_NEW_CITATION_API_OUTPUT
from tha_config import Config


PUBLISH_NEW_CITATION_COMMAND = ADD_NEW_CITATION_API_OUTPUT[0]


class TestBroker(BrokerBase):
    def __init__(self, queue_name: str, listen_to: str):
        self._listen_to = listen_to
        config = Config()
        self.results = []
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name=config.NETWORK_HOST_NAME,
            exchange_name="main",
            queue_name=queue_name,
        )

    async def start(self):
        await self.connect()
        await self.add_message_handler(
            routing_key=self._listen_to, callback=self.handle_message
        )

    async def handle_message(self, message):
        body = self.decode_message(message)
        self.results.append(body)


@pytest.fixture(scope="session")
def publish_new_citation_broker():
    """Instantiate a broker to handle the PUBLISH_NEW_CITATION event."""
    # results will be available via broker.results
    broker = TestBroker(queue_name="test_broker", listen_to="event.emitted")
    return broker


@pytest.fixture(scope="session")
async def setup_add_new_citation_events(publish_new_citation_broker):
    """
    Asynchronously publish the message via the broker and await a result.
    """

    # setup test broker
    broker = publish_new_citation_broker

    await broker.start()

    command = PUBLISH_NEW_CITATION_COMMAND
    msg = broker.create_message(body=command)
    await broker.publish_one(
        message=msg,
        routing_key="command.writemodel",
    )
    start = datetime.utcnow()
    timeout = timedelta(seconds=5)
    while datetime.utcnow() - timeout <= start:
        if len(broker.results) > 0:
            break
        else:
            await asyncio.sleep(0.1)
    assert len(broker.results) > 0, "No events were received"


@pytest.fixture(scope="session")
def add_new_citation_events(publish_new_citation_broker):
    events = [
        from_dict(event_dict) for event_dict in publish_new_citation_broker.results[0]
    ]
    return events


@pytest.fixture(scope="session")
def summary_added(add_new_citation_events):
    return add_new_citation_events[0]


@pytest.fixture(scope="session")
def citation_added(add_new_citation_events):
    return add_new_citation_events[1]


@pytest.fixture(scope="session")
def person_added(add_new_citation_events):
    return add_new_citation_events[2]


@pytest.fixture(scope="session")
def place_added(add_new_citation_events):
    return add_new_citation_events[3]


@pytest.fixture(scope="session")
def time_added(add_new_citation_events):
    return add_new_citation_events[4]


@pytest.fixture(scope="session")
def meta_added(add_new_citation_events):
    return add_new_citation_events[5]


@pytest.mark.asyncio
async def test_run_test(setup_add_new_citation_events):
    # this test runs the `add_new_citation_events` coroutine, making
    # its results available to all following tests
    await setup_add_new_citation_events


@pytest.mark.parametrize(
    "index,value",
    [
        (0, "SUMMARY_ADDED"),
        (1, "CITATION_ADDED"),
        (2, "PERSON_ADDED"),
        (3, "PLACE_ADDED"),
        (4, "TIME_ADDED"),
        (5, "META_ADDED"),
    ],
)
def test_add_new_citation_event_types(index, value, add_new_citation_events):
    assert getattr(add_new_citation_events[index], "type") == value


def test_add_new_citation_event_ids_are_uuids(add_new_citation_events):
    for event in add_new_citation_events:
        assert UUID(event.payload.id)


def test_add_new_citation_returns_same_transaction_ids(add_new_citation_events):
    transaction_id = add_new_citation_events[0].transaction_id
    for event in add_new_citation_events:
        assert event.transaction_id == transaction_id


def test_add_new_citation_transaction_ids_are_uuids(add_new_citation_events):
    for event in add_new_citation_events:
        assert UUID(event.transaction_id)


@pytest.mark.parametrize(
    "attr,value",
    [
        ("user_id", PUBLISH_NEW_CITATION_COMMAND["user"]),
        ("app_version", PUBLISH_NEW_CITATION_COMMAND["app_version"]),
        ("timestamp", PUBLISH_NEW_CITATION_COMMAND["timestamp"]),
        ("index", None),  # index will only be populated after event is persisted
    ],
)
def test_add_new_citation_events_return_same_top_level_attrs(
    attr, value, add_new_citation_events
):
    for event in add_new_citation_events:
        assert getattr(event, attr) == value


def test_add_new_citation_events_return_same_citation_id(add_new_citation_events):
    # unpack events
    add_summary = add_new_citation_events[0]
    add_citation = add_new_citation_events[1]
    add_person = add_new_citation_events[2]
    add_place = add_new_citation_events[3]
    add_time = add_new_citation_events[4]
    add_meta = add_new_citation_events[5]

    citation_id = add_citation.payload.id
    assert add_summary.payload.citation_id == citation_id
    assert add_person.payload.citation_id == citation_id
    assert add_place.payload.citation_id == citation_id
    assert add_time.payload.citation_id == citation_id
    assert add_meta.payload.citation_id == citation_id


def test_citation_added_text(citation_added):
    assert (
        citation_added.payload.text == PUBLISH_NEW_CITATION_COMMAND["payload"]["text"]
    )


def test_summary_added_text(summary_added):
    assert (
        summary_added.payload.text
        == PUBLISH_NEW_CITATION_COMMAND["payload"]["summary"]["text"]
    )


@pytest.mark.parametrize(
    "adm_attr,api_attr",
    [("name", "name"), ("citation_start", "start_char"), ("citation_end", "stop_char")],
)
def test_add_new_person(adm_attr, api_attr, person_added):
    person_added = add_new_citation_events[2]
    tag = PUBLISH_NEW_CITATION_COMMAND["payload"]["tags"][0]
    assert getattr(person_added.payload, adm_attr) == tag[api_attr]


@pytest.mark.parametrize(
    "adm_attr,api_attr",
    [
        ("name", "name"),
        ("citation_start", "start_char"),
        ("citation_end", "stop_char"),
        ("latitude", "latitude"),
        ("longitude", "longitude"),
        ("geo_shape", "geoshape"),
    ],
)
def test_add_new_place(adm_attr, api_attr, place_added):
    tag = PUBLISH_NEW_CITATION_COMMAND["payload"]["tags"][1]
    assert getattr(place_added.payload, adm_attr) == tag.get(api_attr, None)


@pytest.mark.parametrize(
    "adm_attr,api_attr",
    [("name", "name"), ("citation_start", "start_char"), ("citation_end", "stop_char")],
)
def test_add_new_time(adm_attr, api_attr, time_added):
    tag = PUBLISH_NEW_CITATION_COMMAND["payload"]["tags"][2]
    assert getattr(time_added.payload, adm_attr) == tag[api_attr]


@pytest.mark.parametrize("attr", ["title", "author", "publisher"])
def test_add_meta_fields(attr, meta_added):
    assert (
        getattr(meta_added.payload, attr)
        == PUBLISH_NEW_CITATION_COMMAND["payload"]["meta"][attr]
    )


def test_add_meta_kwargs(meta_added):
    command = deepcopy(PUBLISH_NEW_CITATION_COMMAND)
    meta = command["payload"]["meta"]
    for field in ("title", "author", "publisher"):
        meta.pop(field)
    assert meta_added.payload.kwargs == meta


@pytest.mark.asyncio
async def test_cleanup(publish_new_citation_broker):
    try:
        await publish_new_citation_broker.cancel()
    except RuntimeError:
        pass
