"""
SQLAlchemy integration for the History Atlas History service.
Provides read-only access to the database.

"""

import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from abstract_domain_model.transform import from_dict
from event_schema.EventSchema import Event, Base


log = logging.getLogger(__name__)


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def get_event_generator(self, last_index: Union[int, None] = None):
        """
        Returns a generator iterating through events :last_index: + 1.
        """
        log.info(f"Creating an event playback generator")
        if not last_index:
            return self.__event_generator(1)
        return self.__event_generator(last_index + 1)

    def __event_generator(self, start_id) -> Event:
        id = start_id
        while True:
            with Session(self._engine, future=True) as sess:
                db_obj = sess.execute(
                    select(Event).where(Event.index == id)
                ).scalar_one_or_none()
                if not db_obj:
                    log.info("Finished event generator")
                    return
                event_dict = db_obj.to_dict()
                event = from_dict(event_dict)
            yield event
            id += 1
