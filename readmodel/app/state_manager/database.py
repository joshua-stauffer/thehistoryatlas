"""
SQLAlchemy integration for the History Atlas Read Model service.
Provides read and write access to the Query database.
"""

import asyncio
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from .schema import Base, Citation, TagInstance, Time, Person, Place

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config, stm_timeout: int=5):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.__short_term_memory = dict()
        self.__stm_timeout = stm_timeout

    def create_citation(self, transaction_guid, citation_guid, text) -> None:
        """Initializes a new citation in the database.
        
        Temporarily caches the new citation id for following operations."""
        c = Citation(
                guid=citation_guid,
                text=text)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(c)
            # save this id in memory for a few seconds
            self.add_to_stm(
                key=transaction_guid,
                value=c.id)

    def handle_person_update(self,
        transaction_guid: str,
        person_guid: str,
        citation_guid: str,
        person_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool
        ) -> None:
        """Accepts the data from a person event persists it to the database."""

        with Session(self._engine, future=True) as sess, sess.begin():       
            # resolve person
            if is_new:
                person = Person(
                    guid=person_guid,
                    names=person_name)
            else:
                person = sess.execute(
                    select(Person).where(Person.guid == person_guid)
                ).scalar_one()
            # resolve citation
            citation_id = self.__short_term_memory.get(transaction_guid)
            if not citation_id:
                citation_id = sess.execute(
                    select(Citation).where(Citation.guid == citation_guid)
                ).scalar_one().id
            # create Tag Instance
            tag = TagInstance(
                citation_id=citation_id,
                tag=person,
                start_char=start_char,
                stop_char=stop_char)
            sess.add_all([person, tag])
        


    def add_to_stm(self, key, value):
        """Adds a value from an emitted event to the short term memory"""
        self.__short_term_memory[key] = value
        asyncio.create_task(self.__rm_from_stm(key))
        return
    
    async def __rm_from_stm(self, key):
        """internal method to clean up stale values from the stm"""
        await asyncio.sleep(self.__stm_timeout)
        del self.__short_term_memory[key]
