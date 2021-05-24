"""SQLAlchemy database schema for the Geo Service.

May 21st 2021
"""

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('place_id', Integer, ForeignKey('places.id')),
    Column('name_id', Integer, ForeignKey('names.id'))
)

class Name(Base):
    """Model representing a single name"""

    __tablename__ = 'names'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    places = relationship(
        "Place",
        secondary=association_table,
        back_populates='names')

    def __repr__(self) -> str:
        return f'Name: {self.name}'

class Place(Base):
    """Model representing a single coordinate location or geoshape"""

    __tablename__ = 'places'

    id = Column(Integer, primary_key=True)
    geoname_id = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    geoshape = Column(String)
    modification_date = Column(String)

    names = relationship(
        "Name",
        secondary=association_table,
        back_populates='places')

    def __repr__(self) -> str:
        return f'Place( latitude: {self.latitude}, longitude: {self.longitude}, geoshape: {self.geoshape[:20]}...)'

class UpdateTracker(Base):
    """Model tracking database snapshots"""

    __tablename__ = 'update_tracker'

    id = Column(Integer, primary_key=True)
    timestamp = Column(String(36))          # time accessed

    def __repr__(self) -> str:
        return f'UpdateTracker( id: {self.id}, timestamp: {self.timestamp})'

