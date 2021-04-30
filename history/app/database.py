"""
SQLAlchemy integration for the History Atlas History service.
Provides read-only access to the database.

This currently requires the database to fit in working memory.
Better solution in the works!
"""

import json
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from event_schema.EventSchema import Event, Base

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config):
        log.info('Making database connection.')
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)

    def get_events(self, last_id: Union[int, None]=None):
        """Creates a generator to return all events after the last seen.
        params:
            last_id: the last event number processed by your application
                     if None, will stream entire database from beginning
                     0 < last_id
        returns:
            generator streaming all events after the last you've seen
        """
        log.info(f'Creating an event playback generator')
        if not last_id:
            return self.__event_generator(1)
        return self.__event_generator(last_id + 1)
        
    def __event_generator(self, start_id):
        res = True
        id = start_id
        while res:
            with Session(self._engine, future=True) as sess:
                res = sess.execute(
                    select(Event).where(Event.id == id)
                ).scalar_one_or_none()
                if not res:
                    log.info('Finished event generator')
                    return
                jsonified = self.to_json(res)
            yield jsonified
            id += 1

    def get_events_in_chron_order(self, start_id: int=0):
        """Acts as a generator for events in database, and streams them to 

        When optional param: start_id is provided events will only be
        included which have ids higher than start_id
        
        Sorts based on event id."""
        
        log.info('Querying for events in chronological order')
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

        log.info('Querying for events in priority order')
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
        log.debug(f'JSONifying the event {event}')
        return json.dumps({
            "id": event.id,
            "type": event.type,
            "transaction_guid": event.transaction_guid,
            "app_version": event.app_version,
            "timestamp": event.timestamp,
            "user": event.user,
            "payload": json.loads(event.payload),
        })
