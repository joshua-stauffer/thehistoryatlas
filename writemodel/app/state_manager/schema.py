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
