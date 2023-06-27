import logging
from dataclasses import asdict
from typing import List, Dict

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.transform import from_dict
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.eventstore.event_schema import Event as EventModel, Base

log = logging.getLogger(__name__)


class Database:
    def __init__(self, engine: Engine):
        self._engine = engine
        # initialize the db
        Base.metadata.create_all(self._engine)

    def commit_events(self, events: List[Event]) -> list[Event]:
        """Commit an event to the database"""
        log.info(f"Committing event {events} to the event store database.")

        with Session(self._engine, future=True) as session:
            emitted_events: List[EventModel] = [
                EventModel(
                    type=event.type,
                    transaction_id=event.transaction_id,
                    app_version=event.app_version,
                    timestamp=event.timestamp,
                    user_id=event.user_id,
                    payload=asdict(event.payload),
                )
                for event in events
            ]
            session.add_all(emitted_events)
            session.commit()

            persisted_events = [from_dict(e.to_dict()) for e in emitted_events]

        log.debug(
            f"returning persisted events {persisted_events} from the database store"
        )
        return persisted_events
