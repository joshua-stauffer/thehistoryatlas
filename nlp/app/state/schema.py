"""SQLAlchemy database schema for the NLP service.

May 19th 2021
"""

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, BOOLEAN
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

class AnnotatedCitation(Base):
    """Event representing a single annotated citation."""

    __tablename__ = 'annotated_citation'

    id = Column(INTEGER, primary_key=True)
    text = Column(VARCHAR)
    entities = relationship('Entity', back_populates='annotated_citation')

    def __repr__(self):
        return f"AnnotatedCitation(id: {self.id}, text: {self.text})"

class Entity(Base):
    """Event representing an entity tagged in an annotation."""

    __tablename__ = 'entity'

    id = Column(INTEGER, primary_key=True)
    type = Column(VARCHAR)               # PERSON PLACE TIME
    start_char = Column(INTEGER)
    stop_char = Column(INTEGER)
    annotated_citation_id = Column(INTEGER, ForeignKey('annotated_citation.id'))
    annotated_citation = relationship('AnnotatedCitation', back_populates='entities')

    def __repr__(self):
        return f'Entity(id: {self.id}, type: {self.type}, start_char: {self.start_char}, ' + \
               f'stop_char: {self.stop_char})'

class Init(Base):
    """Event which tracks if this database instance has been initialized or not."""

    __tablename__ = 'init'

    id = Column(INTEGER, primary_key=True)
    is_initialized = Column(BOOLEAN)

    def __repr__(self):
        if self.is_initialized:
            answer = 'is'
        else:
            answer = 'is not'
        return f'This database {answer} initialized.'
