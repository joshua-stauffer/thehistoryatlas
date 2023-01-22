from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import VARCHAR, UUID, JSONB, INTEGER

Base = declarative_base()


class IDLookup(Base):
    """
    Associate Wiki IDs with the History Atlas IDs.
    """

    __tablename__ = "id_lookup"

    wiki_id = Column(VARCHAR, unique=True, primary_key=True)
    wiki_type = Column(VARCHAR, nullable=False)
    entity_type = Column(VARCHAR, nullable=True)
    local_id = Column(UUID(as_uuid=False), nullable=True)
    last_checked = Column(VARCHAR)
    last_modified_at = Column(VARCHAR)


class WikiQueue(Base):
    """Wiki Items to be processed prior to entering the IDLookup table."""

    __tablename__ = "wiki_queue"

    wiki_id = Column(VARCHAR, primary_key=True)
    wiki_url = Column(VARCHAR)
    entity_type = Column(VARCHAR, nullable=False)
    wiki_type = Column(VARCHAR, nullable=False)
    errors = Column(JSONB, default={})
    time_added = Column(VARCHAR, nullable=False)


class Config(Base):
    """Values for application use."""

    __tablename__ = "config"

    id = Column(INTEGER, primary_key=True, default=1)
    last_person_search_offset = Column(INTEGER, default=0)
