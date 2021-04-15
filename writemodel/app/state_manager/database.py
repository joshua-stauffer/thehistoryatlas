"""
SQLAlchemy integration for the History Atlas WriteModel service.
Provides read and write access to the Command Validator database.

"""

import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from .schema import Base, PersonAggregate, PersonName, PlaceAggregate, PlaceName

class Database:

    def __init__(self, config):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True
        )
        # initialize the db
        Base.metadata.create_all(self._engine)

    # methods for interacting with the PersonAggregate

    def add_person(self, name: str, guid: str):
        """Adds a person to the write database.
        
        params:
            name: str
            guid: str
        """

        person = PersonAggregate(guid=guid)
        name = PersonName(name=name, person=person)

        with Session(self._engine, future=True) as sess, sess.begin():
            sess.add(person)
            sess.add(name)

        return        

    def add_name_to_person(self, name: str, guid: str):
        """Add a new moniker to existing person.
        
        params:
            name: str
            guid: str
        """

        with Session(self._engine, future=True) as sess, sess.begin():
            
            person = sess.execute(
                select(PersonAggregate).filter_by(guid=guid)
            ).scalar_one()
            person_name = PersonName(name=name, person=person)
            sess.add(person_name)

    def get_names_of_person(self, person_guid):
        """returns a list of all names associated with person.
        """

        with Session(self._engine, future=True) as sess:
            
            person = sess.execute(
                select(PersonAggregate).filter_by(guid=person_guid)
            ).scalar_one()
            names = person.names

        return names

    # methods for interacting with the PlaceAggregate

