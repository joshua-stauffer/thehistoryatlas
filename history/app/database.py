"""
SQLAlchemy integration for the History Atlas History service.
Provides read-only access to the database.

This currently requires the database to fit in working memory.
Better solution in the works!
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

    def get_events_in_chron_order(self, start_id: int=0):
        """Acts as a generator for events in database, and streams them to 

        When optional param: start_id is provided events will only be
        included which have ids higher than start_id
        
        Sorts based on event id."""
        
        stmt = select(Event) \
            .where(Event.id > start_id) \
            .order_by(Event.id)

        with Session(self._engine, future=True) as session, session.begin():
            results = session.execute(stmt)
            jsonified_results = [self.to_json(r) for r in results.scalars()]
        return jsonified_results

    def get_events_in_priority_order(self, start_id: int=0):        
        """Returns an iterable of events in the database.

        When optional param: start_id is provided events will only be
        included which have ids higher than start_id

        Sorts first based on priority to allow annulling events (0)
        to float to the top, and second on event id.
        """

        stmt = select(Event) \
            .where(Event.id > start_id) \
            .order_by(Event.priority, Event.id)

        with Session(self._engine, future=True) as session, session.begin():
            results = session.execute(stmt)
            jsonified_results = [self.to_json(r) for r in results.scalars()]
        return jsonified_results

    @staticmethod
    def to_json(event):
        """returns a json string representation of this Event"""
        print('trying to jsonify ', event)
        print(event.id)
        return json.dumps({
            "id": event.id,
            "type": event.type,
            "timestamp": event.timestamp,
            "user": event.user,
            "payload": event.payload,
            "priority": event.priority
        })
