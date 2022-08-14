"""
SQLAlchemy integration for the History Atlas WriteModel service.
Provides read and write access to the Command Validator database.
"""

import asyncio
import logging
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from .schema import Base
from .schema import CitationHash
from .schema import GUID
from .schema import History

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
            log.info(f'Matched GUID {guid_to_test} to type {tmp_type} in STM')
            return tmp_type

        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(GUID).where(GUID.value==guid_to_test)
            ).scalar_one_or_none()
            log.debug(f'Database: searching for GUID and found {result}')
            if result:
                return result.type
            else:
                log.debug(f'Found no existing result for GUID {guid_to_test}')
                return None

    def add_guid(self, value, type):
        """Adds a new record to the GUID lookup table"""
        record = GUID(value=value, type=type)
        with Session(self._engine, future=True) as session:
            res = session.execute(select(GUID).where(GUID.value==value)).scalar_one_or_none()
            if res:
                raise Exception(f'Caught duplicate row for type {type} guid {value}')
            session.add(record)
            session.commit()

    def add_to_stm(self, key, value):
        """Adds a value from an emitted event to the short term memory"""
        self.__short_term_memory[key] = value
        asyncio.create_task(self.__rm_from_stm(key))
        log.debug(f'Added key {key} to short term memory')
        return
    
    async def __rm_from_stm(self, key):
        """internal method to clean up stale values from the stm"""
        await asyncio.sleep(self.__stm_timeout)
        log.debug(f'Removing key {key} from short term memory.')
        del self.__short_term_memory[key]

    # HISTORY MANAGEMENT

    def check_database_init(self) -> int:
        """Checks database for the most recent event id. Returns None if 
        database isn't initialized yet, otherwise most recent id."""
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(History)
            ).scalar_one_or_none()
            if not res:
                # initialize with default row
                session.add(History())
                session.commit()
                return 0
            return res.latest_event_id

    def update_last_event_id(self, event_id: int) -> int:
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(History)
            ).scalar_one_or_none()
            if not res:
                res = History(latest_event_id=event_id)
            # for now, not checking if id is out of order
            res.latest_event_id = event_id
            session.add(res)
            session.commit()
