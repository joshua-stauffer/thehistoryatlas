"""SQLAlchemy database schema for the Geo Service.

May 21st 2021
"""

from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT

Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('place_id', INTEGER, ForeignKey('places.id')),
    Column('name_id', INTEGER, ForeignKey('names.id'))
)

class Name(Base):
    """Model representing a single name"""

    __tablename__ = 'names'

    id = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR, unique=True)
    places = relationship(
        "Place",
        secondary=association_table,
        back_populates='names')

    def __repr__(self) -> str:
        return f'Name: {self.name}'

class Place(Base):
    """Model representing a single coordinate location or geoshape"""

    __tablename__ = 'places'

    id = Column(INTEGER, primary_key=True)
    geoname_id = Column(INTEGER)
    latitude = Column(FLOAT)
    longitude = Column(FLOAT)
    geoshape = Column(VARCHAR)
    modification_date = Column(VARCHAR)

    names = relationship(
        "Name",
        secondary=association_table,
        back_populates='places')

    def __repr__(self) -> str:
        return f'Place( latitude: {self.latitude}, longitude: {self.longitude}, geoshape: {self.geoshape[:20]}...)'

class UpdateTracker(Base):
    """Model tracking database snapshots"""

    __tablename__ = 'update_tracker'

    id = Column(INTEGER, primary_key=True)
    timestamp = Column(VARCHAR)          # time accessed

    def __repr__(self) -> str:
        return f'UpdateTracker( id: {self.id}, timestamp: {self.timestamp})'

