"""
SQLAlchemy database schema for the Command Manager database, as part of
the WriteModel service.
"""

import json
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PersonAggregate(Base):
    """Represents the basic Person aggregate"""

    __tablename__ = 'people_aggregate'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), nullable=False)

    names = relationship('PersonName', back_populates='person')

    def __repr__(self):
        return f'PersonAggregate(id: {self.id}, guid: {self.guid})'

class PersonName(Base):
    """Represents a database table of names already associated with people"""

    __tablename__ = 'people_names'

    id = Column(Integer, primary_key=True)
    person_id = Column(ForeignKey(PersonAggregate.id))
    name = Column(String)

    person = relationship(PersonAggregate, back_populates='names')

    def __repr__(self):
        return f'{self.name}'

class PlaceAggregate(Base):
    __tablename__ = 'places_aggregate'

    id = Column(Integer, primary_key=True)
    guid = Column(String(36), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)

    names = relationship('PlaceName')

class PlaceName(Base):
    """Represents a database table of names already associated with places"""

    __tablename__ = 'place_names'

    id = Column(Integer, primary_key=True)
    parent_id = Column(ForeignKey(PlaceAggregate.id))
    name = Column(String)
