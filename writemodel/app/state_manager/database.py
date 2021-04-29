"""
SQLAlchemy integration for the History Atlas WriteModel service.
Provides read and write access to the Command Validator database.
"""

import asyncio
import json
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from .schema import Base, CitationHash, GUID

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.__short_term_memory = dict()

    def check_citation_for_uniqueness(self, text_hash) -> Union[str, None]:
        """Looks for hash in table CitationHash and returns GUID if found"""
        
        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(CitationHash).where(CitationHash.hash==text_hash)
            ).scalar_one_or_none()
            logging.debug(f'Database: searching for citation and found {result}')
            if result:
                # add call to short term memory, but can't block..
                pass
            return result

    def add_citation_hash(self, hash, GUID):
        """Adds a new record to the citation hash table"""
        record = CitationHash(hash=hash, GUID=GUID)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(record)

    def check_guid_for_uniqueness(self, guid_to_test: str) -> Union[str, None]:
        """Looks for guid and returns type if found"""

        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(GUID).where(GUID.value==guid_to_test)
            ).scalar_one_or_none()
            logging.debug(f'Database: searching for GUID and found {result}')
            return result.type

    def add_guid(self, value, type):
        """Adds a new record to the GUID lookup table"""
        record = GUID(value=value, type=type)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(record)

    async def add_result_to_stm(self, key, value, timeout):
        self.__short_term_memory[key] = value
        await asyncio.sleep(timeout)
        del self.__short_term_memory[key]
