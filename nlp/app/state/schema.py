"""SQLAlchemy database schema for the NLP service.

May 19th 2021
"""

from sqlalchemy import Column, Enum
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, BOOLEAN, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()


class AnnotatedCitation(Base):
    """Model representing a single annotated citation."""

    __tablename__ = "annotated_citations"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    text = Column(VARCHAR, nullable=False)
    entities = relationship("Entity", back_populates="annotated_citation")

    def __repr__(self):
        return f"AnnotatedCitation(id: {self.id}, text: {self.text})"


class Entity(Base):
    """Model representing an entity tagged in an annotation."""

    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    type = Column(Enum("PERSON", "PLACE", "TIME", name="entity_type"), nullable=False)
    start_char = Column(INTEGER, nullable=False)
    stop_char = Column(INTEGER, nullable=False)
    annotated_citation_id = Column(
        UUID, ForeignKey("annotated_citations.id"), nullable=False
    )
    annotated_citation = relationship("AnnotatedCitation", back_populates="entities")

    def __repr__(self):
        return (
            f"Entity(id: {self.id}, type: {self.type}, start_char: {self.start_char}, "
            + f"stop_char: {self.stop_char})"
        )


class Init(Base):
    """Model which tracks if this database instance has been initialized or not."""

    __tablename__ = "init"

    id = Column(INTEGER, primary_key=True)
    is_initialized = Column(BOOLEAN)

    def __repr__(self):
        if self.is_initialized:
            answer = "is"
        else:
            answer = "is not"
        return f"This database {answer} initialized."
