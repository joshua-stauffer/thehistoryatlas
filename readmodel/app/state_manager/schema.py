"""SQLAlchemy database schema for the Read Model service.

May 3rd 2021
"""

from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

class Citation(Base):
    """Model representing citations and their meta data, with links to
    their tags"""

    __tablename__ = 'citations'
    id = Column(Integer, primary_key=True)
    guid = Column(String(36))
    text = Column(String)
    # meta data stored as json string with arbitrary fields
    # not planning on querying against this, just need it available
    meta = Column(String)
    # specific instances of tags anchored in the citation text
    tags = relationship('TagInstance', back_populates='citation')

    def __repr__(self):
        return f'Citation(id: {self.id}, text: {self.text}, meta: {self.meta}, ' + \
               f'timetag: {self.timetag.name})'

class TagInstance(Base):
    """Model representing the connection point between a citation slice and
    a tag."""

    __tablename__ = 'taginstances'
    id = Column(Integer, primary_key=True)
    start_char = Column(Integer)
    stop_char = Column(Integer)
    # parent citation
    citation_id = Column(Integer, ForeignKey('citations.id'))
    citation = relationship('Citation', back_populates='tags')
    # parent tag
    tag_id = Column(Integer, ForeignKey('tags.id'))
    tag = relationship('Tag', back_populates='tag_instances')

    def __repr__(self):
        return f''

class Tag(Base):
    """Base class for time, person, and place tags"""

    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    guid = Column(String(36))
    type = Column(String(8))    # 'TIME' | 'PERSON' | 'PLACE'
    tag_instances = relationship('TagInstance', back_populates='tag')

    __mapper_args__ = {
        'polymorphic_identity': 'TAG',
        'polymorphic_on': type
    }

class Time(Tag):

    __tablename__ = 'time'
    id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    name = Column(String(32))

    __mapper_args__ = {
        'polymorphic_identity': 'TIME'
    }

    def __repr__(self):
        return f'TimeTag(id: {self.id}, name: {self.name})'

class Person(Tag):

    __tablename__ = 'person'
    id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    names = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'PERSON'
    }

    def __repr__(self):
        return f'PersonTag(id: {self.id}, names: {self.name})'

class Place(Tag):

    __tablename__ = 'place'

    id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    names = Column(String)
    latitude= Column(Float)
    longitude = Column(Float)
    geoshape = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'PLACE'
    }

    def __repr__(self):
        return f'PlaceTag(id: {self.id}, names: {self.name})'
