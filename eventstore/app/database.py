"""
SQLAlchemy integration for the History Atlas EventStore service.
Provides write only access to the canonical database.
"""

import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from schema import Event, Base

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)

    def commit_event(self, event):
        """Commit an event to the database"""

        event = Event(
            type=event.get('type'),                         # string representing EventType
            timestamp=event.get('timestamp'),               # string timestamp
            user=event.get('user'),                         # string user GUID
            payload=json.dumps(event.get('payload')),       # arbitrary json string
            priority=event.get('priority')                  # 0 or 1
        )

        with Session(self._engine, future=True) as session:
            session.add(event)
            session.commit()
            json_event = event.to_json()
        
        return json_event
