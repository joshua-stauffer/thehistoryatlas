"""SQLAlchemy database schema for the Read Model service.

May 3rd 2021
"""

from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

class Citation(Base):
    """Represents Citations and their meta data"""

    __tablename__ = 'citations'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), primary_key=True)
    text = Column(String)

    # meta data stored as json string with arbitrary fields
    # not planning on querying against this, just need it available
    meta = Column(String)

    timetag_id = Column(Integer, ForeignKey('timetags.id'))
    timetag = relationship('TimeTag', back_populates='citations')

    def __repr__(self):
        return f'Citation(id: {self.id}, text: {self.text}, meta: {self.meta}, ' + \
               f'timetag: {self.timetag.name})'

class TimeTag(Base):
    """Model representing a single unique time label. Root node in graph.
    Query point of entry for accessing citations on the time axis."""

    __tablename__ = 'timetags'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), primary_key=True)
    name = String(36)

    citations = relationship('Citation', back_populates='timetag')
    people = relationship('PersonTag', back_populates='timetag')
    places = relationship('PlaceTag', back_populates='timetag')
    tags = 

    def __repr__(self):
        return f'TimeTag(id: {self.id}, name: {self.name}, citations: ' + \
               f'{len(self.citations)}, people: {len(self.people)}, ' + \
               f'places: {len(self.places)})'

class PersonTag(Base):
    """Model representing a single person.
    Query point of entry for accessing citations on the person axis"""

    __tablename__ = 'peopletags'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), primary_key=True)
    names = Column(String)

    timetag_id = Column(Integer, ForeignKey('timetags.id'))
    timetag = relationship('TimeTag', back_populates='people')

    def __repr__(self):
        return f'PersonTag(id: {self.id}, names: {self.names}, ' + \
               f'timetag: {self.timetag.name})'

class PlaceTag(Base):
    """Model representing a single geographic place.
    Query point of entry for accessing citations by the place axis"""

    __tablename__ = 'placetags'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), primary_key=True)
    names = Column(String)
    longitude = Column(Float)
    latitude = Column(Float)
    shape = Column(String)

    timetag_id = Column(Integer, ForeignKey('timetags.id'))
    timetag = relationship('TimeTag', back_populates='places')

    def __repr__(self):
        return f'PlaceTag(id: {self.id}, names: {self.names}, ' + \
               f'longitude: {self.longitude}, latitude: {self.latitude}' + \
               f'shape: {self.shape != None}, timetag: {self.timetag.name})'

class GenericTag(Base):
    """Association table which provides connection between a citation and its tags"""

    __tablename__ = 'generictags'

    id = Column(Integer, primary_key=True)
    type = Column(String(8)) # 'time' | 'person' | 'place'
    tag_guid = Column(String(36))
    start_char = Column(Integer)
    stop_char = Column(Integer)



    def __repr__(self):
        return f'GenericTag(id: {self.id}, type: {self.type}, tag: ' + \
               f'{self.tag_guid}, start: {self.start_char}, stop: {self.stop_char})'