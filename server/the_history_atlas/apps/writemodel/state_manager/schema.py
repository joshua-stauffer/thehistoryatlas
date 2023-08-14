from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import INTEGER, VARCHAR

Base = declarative_base()


class CitationHash(Base):
    """Lookup table of citation text hashes and their associated GUIDs"""

    __tablename__ = "citation_hashes"

    id = Column(INTEGER, primary_key=True)
    hash = Column(VARCHAR(256))
    GUID = Column(VARCHAR(36))

    def __repr__(self):
        return f"CitationHash(\nhash: {self.hash},\nGUID: {self.GUID}\n)"


class GUID(Base):
    """Global lookup table of GUIDs and their types to ensure uniqueness.
    Allows new GUIDs to be generated client-side while providing guarantees
    against collisions, accidental or otherwise"""

    __tablename__ = "guids"

    id = Column(INTEGER, primary_key=True)
    value = Column(VARCHAR(36), unique=True)
    type = Column(VARCHAR(32))  # person? place? citation? meta?

    def __repr__(self):
        return f"GUID( type: {self.type}, value: {self.value})"


class History(Base):

    __tablename__ = "history"

    id = Column(INTEGER, primary_key=True)
    latest_event_id = Column(INTEGER, default=0)
