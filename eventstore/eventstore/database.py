"""
SQLAlchemy integration for the History Atlas EventStore service.
Provides write only access to the canonical database.
"""

import json
import logging
from dataclasses import asdict
from typing import List, Dict

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from abstract_domain_model.transform import from_dict, to_dict
from abstract_domain_model.types import Event
from event_schema.EventSchema import Event as EventModel, Base

log = logging.getLogger(__name__)


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def commit_event(self, synthetic_event: List[Dict]) -> list[Event]:
        """Commit an event to the database"""
        log.info(f"Committing event {synthetic_event} to the event store database.")
        events: List[Event] = [from_dict(event) for event in synthetic_event]
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

        with Session(self._engine, future=True) as session:
            session.add_all(emitted_events)
            session.commit()

        persisted_events = [from_dict(e.to_dict()) for e in emitted_events]

        log.debug(
            f"returning persisted events {persisted_events} from the database store"
        )
        return persisted_events
