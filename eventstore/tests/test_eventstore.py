from dataclasses import asdict

from sqlalchemy.orm import Session

from abstract_domain_model.types import Event
from .seed import SYNTHETIC_EVENTS
from event_schema.EventSchema import Event as EventModel


def test_commit_event_persists_synthetic_events(db):
    event = SYNTHETIC_EVENTS[0]
    persisted_events = db.commit_event(event)
    assert isinstance(persisted_events, list)
    with Session(db._engine, future=True) as session:
        for event in persisted_events:
            assert isinstance(event, Event)
            db_row = (
                session.query(EventModel).filter(EventModel.index == event.index).one()
            )
            assert event.index == db_row.index
            assert event.user_id == db_row.user_id
            assert event.type == db_row.type
            assert event.transaction_id == db_row.transaction_id
            assert event.app_version == db_row.app_version
            assert event.timestamp == db_row.timestamp
            assert asdict(event.payload) == db_row.payload
