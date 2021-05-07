from app.event_store import EventStore

def test_eventstore():
    store = EventStore()
    assert store != None
