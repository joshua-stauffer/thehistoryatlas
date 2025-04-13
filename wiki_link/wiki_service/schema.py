import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import VARCHAR, UUID, JSONB, INTEGER, TIMESTAMP

Base = declarative_base()


class IDLookup(Base):
    """
    Associate Wiki IDs with the History Atlas IDs.
    """

    __tablename__ = "id_lookup"

    wiki_id = Column(VARCHAR, unique=True, primary_key=True)
    entity_type = Column(VARCHAR, nullable=True)
    local_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    last_checked = Column(TIMESTAMP(timezone=True), nullable=False)
    last_modified_at = Column(TIMESTAMP(timezone=True), nullable=False)


class WikiQueue(Base):
    """Wiki Items to be processed prior to entering the IDLookup table."""

    __tablename__ = "wiki_queue"

    wiki_id = Column(VARCHAR, primary_key=True)
    wiki_url = Column(VARCHAR)
    entity_type = Column(VARCHAR, nullable=False)
    errors = Column(JSONB, default={})
    time_added = Column(TIMESTAMP(timezone=True), nullable=False)

    # Index for fast retrieval of oldest items
    __table_args__ = (Index("idx_wiki_queue_time_added", "time_added"),)


class FactoryResult(Base):
    __tablename__ = "factory_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wiki_id = Column(VARCHAR, nullable=False)
    factory_label = Column(VARCHAR, nullable=False)
    factory_version = Column(INTEGER, nullable=False)
    errors = Column(JSONB, default={})
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )


class CreatedEvent(Base):
    __tablename__ = "created_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factory_result_id = Column(
        UUID(as_uuid=True), ForeignKey("factory_results.id"), nullable=False
    )
    primary_entity_id = Column(VARCHAR, nullable=False)
    secondary_entity_id = Column(VARCHAR, nullable=True)
    server_id = Column(UUID(as_uuid=True), nullable=True)
    event = Column(JSONB, nullable=True)


class Config(Base):
    """Values for application use."""

    __tablename__ = "config"

    id = Column(INTEGER, primary_key=True, default=1)
    last_person_search_offset = Column(INTEGER, default=0)
    last_works_of_art_search_offset = Column(INTEGER, default=0)
    last_books_search_offset = Column(INTEGER, default=0)
    last_orations_search_offset = Column(INTEGER, default=0)
