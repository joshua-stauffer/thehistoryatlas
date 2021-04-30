"""
SQLAlchemy integration for the History Atlas EventStore service.
Provides write only access to the canonical database.
"""

import json
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from event_schema.EventSchema import Event, Base

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def commit_event(self, event):
        """Commit an event to the database"""
        log.info(f'Committing event {event} to the event store database.')
        event = Event(
            type=event.get('type'),                         # string representing EventType
            transaction_guid=event.get('transaction_guid'), # group atomic events together by command
            app_version=event.get('app_version'),           # future proof(ish)
            timestamp=event.get('timestamp'),               # string timestamp
            user=event.get('user'),                         # string user GUID
            payload=json.dumps(event.get('payload')),       # arbitrary json string
        )

        with Session(self._engine, future=True) as session:
            session.add(event)
            session.commit()
            persisted_event = event.to_dict()
        
        log.debug(f'returning persisted event {persisted_event} from the database store')
        return persisted_event
