"""
SQLAlchemy database schema for the Command Manager database, as part of
the WriteModel service.
"""

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CitationHash(Base):
    """Lookup table of citation text hashes and their associated GUIDs"""

    __tablename__ = 'citation_hashes'

    id = Column(Integer, primary_key=True)
    hash = Column(String(256))
    GUID = Column(String(36))

    def __repr__(self):
        return f"CitationHash(\nhash: {self.hash},\nGUID: {self.GUID}\n)"

class GUID(Base):
    """Global lookup table of GUIDs and their types to ensure uniqueness.
    Allows new GUIDs to be generated client-side while providing guarantees 
    against collisions, accidental or otherwise"""

    __tablename__ = 'guids'

    id = Column(Integer, primary_key=True)
    value = Column(String(36))
    type = Column(String(32))       # person? place? citation? meta?

    def __repr__(self):
        return f"GUID( type: {self.type}, value: {self.value})"

class History(Base):

    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)
    latest_event_id = Column(Integer, default=0)
