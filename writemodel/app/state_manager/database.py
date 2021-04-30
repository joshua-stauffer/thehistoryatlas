"""
SQLAlchemy integration for the History Atlas WriteModel service.
Provides read and write access to the Command Validator database.
"""

import asyncio
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from .schema import Base, CitationHash, GUID

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config, stm_timeout: int=60):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.__short_term_memory = dict()
        self.__stm_timeout = stm_timeout

    def check_citation_for_uniqueness(self, text_hash) -> Union[str, None]:
        """Looks for hash in table CitationHash and returns GUID if found"""

        if tmp_guid := self.__short_term_memory.get(text_hash):
            log.info('Matched a hashed citation in short term memory')
            return tmp_guid
        
        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(CitationHash).where(CitationHash.hash==text_hash)
            ).scalar_one_or_none()
            log.debug(f'Database: searching for citation and found {result}')
            if result:
                return result.GUID
            else:
                return None

    def add_citation_hash(self, hash, GUID):
        """Adds a new record to the citation hash table"""
        record = CitationHash(hash=hash, GUID=GUID)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(record)

    def check_guid_for_uniqueness(self, guid_to_test: str) -> Union[str, None]:
        """Looks for guid and returns type if found"""

        if tmp_type := self.__short_term_memory.get(guid_to_test):
            log.info('Matched a GUID in short term memory')
            return tmp_type

        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(GUID).where(GUID.value==guid_to_test)
            ).scalar_one_or_none()
            log.debug(f'Database: searching for GUID and found {result}')
            if result:
                return result.type
            else:
                return None

    def add_guid(self, value, type):
        """Adds a new record to the GUID lookup table"""
        record = GUID(value=value, type=type)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(record)

    def add_to_stm(self, key, value):
        """Adds a value from an emitted event to the short term memory"""
        self.__short_term_memory[key] = value
        asyncio.create_task(self.__rm_from_stm(key))
        return
    
    async def __rm_from_stm(self, key):
        """internal method to clean up stale values from the stm"""
        await asyncio.sleep(self.__stm_timeout)
        del self.__short_term_memory[key]
