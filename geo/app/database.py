"""SQLAlchemy integration for the History Atlas Geo Service.
Stores geographic names and associated coordinates.

May 21st, 2021
"""
from collections import namedtuple
import logging
import json
import os
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.schema import Base
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

    def build_db(self, city_rows: list[CityRow]):
        ...