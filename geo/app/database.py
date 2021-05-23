"""SQLAlchemy integration for the History Atlas Geo Service.
Stores geographic names and associated coordinates.

May 21st, 2021
"""
from collections import namedtuple
from datetime import datetime
import logging
import json
import os
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.schema import Base
from app.schema import Name
from app.schema import Place
from app.schema import UpdateTracker
from app.geonames_data import CityRow

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config):
        self._config = config
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    # db query tools

    def get_coords_by_name(self, name: str):
        """Resolve a geographic name into a list of possible coordinates."""
        with Session(self._engine, future=True) as session:
            name_row = session.execute(
                select(Name).where(Name.name == name)
            ).scalar_one_or_none()
            if not name_row:
                return []
            return [(place.latitude, place.longitude) 
                    for place in name_row.places]
    
    def get_coords_by_name_batch(self, names: list[str]):
        """Resolve a list of place names into a dict where the keys are names 
        and the values are lists of possible coordinates."""
        res = dict()
        with Session(self._engine, future=True) as session:
            for name in names:
                name_row = session.execute(
                    select(Name).where(Name.name == name)
                ).scalar_one_or_none()
                if not name_row:
                    coords = []
                else:
                    coords = [(place.latitude, place.longitude) 
                            for place in name_row.places]
                res[name] = coords
        return res

    # bulk db building tools

    def build_db(self, geodata: list[CityRow]):
        """Fill an empty database with the contents of a geonames file."""

        # allow for data with shape details as well, but handle differently
        if isinstance(geodata[0], CityRow):
            self._build_db_from_city_row(geodata)

        with Session(self._engine, future=True) as session:
            update = UpdateTracker(timestamp=str(datetime.utcnow()))
            session.add(update)
            session.commit()

    def _build_db_from_city_row(self, city_rows: list[CityRow]):
        """Update database with fresh data, taking care to not duplicate
        existing information. This should be run only occasionally, and
        as such its expense is acceptable."""

        with Session(self._engine, future=True) as session:
            for row in city_rows:
                to_commit = list()
                place = session.execute(
                    select(Place).where(Place.geonames_id == row.geonames_id)
                ).scalar_one_or_none()
                if not place:
                    place = Place(
                        geonames_id         = row.geonames_id,
                        latitude            = row.latitude,
                        longitude           = row.longitude,
                        modification_date   = row.modification_date)
                to_commit.append(place)
                names = set([row.name, row.ascii_name, *row.alternate_names.split(',')])
                for spelling in names:
                    # do we need to create a Name for this spelling?
                    name = session.execute(
                        select(Name).where(Name.name == spelling)
                    ).scalar_one_or_none()
                    if not name:
                        name = Name(name=spelling)
                    # does this name already have this place?
                    if name not in name.places:
                        name.places.append(place)
                    to_commit.append(name)
                session.add_all(to_commit)
                session.commit()
