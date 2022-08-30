from abstract_domain_model.types import Event
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
