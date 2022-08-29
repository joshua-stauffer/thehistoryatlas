"""
SQLAlchemy integration for the History Atlas History service.
Provides read-only access to the database.

"""

import json
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from abstract_domain_model.transform import from_dict, to_dict
from event_schema.EventSchema import Event, Base


log = logging.getLogger(__name__)


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def get_event_generator(self, last_id: Union[int, None] = None):
        """Creates a generator to return all events after the last seen.
        params:
            last_id: the last event number processed by your application
                     if None, will stream entire database from beginning
                     0 < last_id
        returns:
            generator streaming all events after the last you've seen
        """
        log.info(f"Creating an event playback generator")
        if not last_id:
            return self.__event_generator(1)
        return self.__event_generator(last_id + 1)

    def __event_generator(self, start_id) -> Event:
        id = start_id
        while True:
            with Session(self._engine, future=True) as sess:
                res = sess.execute(
                    select(Event).where(Event.index == id)
                ).scalar_one_or_none()
                if not res:
                    log.info("Finished event generator")
                    return
                event = from_dict(res.to_dict())
            yield event
            id += 1
