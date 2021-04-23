"""
SQLAlchemy integration for the History Atlas WriteModel service.
Provides read and write access to the Command Validator database.
"""

import json
import logging
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text
from .schema import Base, CitationHash

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)

    def check_citation_for_uniqueness(self, text_hash) -> Union[str, None]:
        """Looks for hash in table CitationHash and returns GUID if found"""
        
        with Session(self._engine, future=True) as sess:
            result = sess.execute(
                select(CitationHash).where(CitationHash.hash==text_hash)
            ).scalar_one_or_none()
            logging.debug(f'Database: searching for citation and found {result}')
            return result

    def add_citation_hash(self, hash, GUID):
        """Adds a new record to the citation hash table"""
        record = CitationHash(hash=hash, GUID=GUID)
        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(record)
