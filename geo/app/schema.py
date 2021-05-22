"""SQLAlchemy database schema for the Geo Service.

May 21st 2021
"""

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

class Place(Base):
    """Model representing a single coordinate location or geoshape"""

    __tablename__ = 'places'

    id = Column(Integer, primary_key=True)
    longitude = Column(Float)
    latitude = Column(Float)
    geoshape = Column(String)

    def __repr__(self) -> str:
        return f''

class Name(Base):
    """Model representing a single name"""

    __tablename__ = 'names'

    id = Column(Integer, primary_key=True)

    def __repr__(self) -> str:
        return f''

class UpdateTracker(Base):
    """Model tracking database snapshots"""

    __tablename__ = 'update_tracker'

    id = Column(Integer, primary_key=True)
    timestamp = Column(String(36))          # time accessed

    def __repr__(self) -> str:
        return f'UpdateTracker( id: {self.id}, timestamp: {self.timestamp})'

