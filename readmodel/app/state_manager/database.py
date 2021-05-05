"""
SQLAlchemy integration for the History Atlas Read Model service.
Provides read and write access to the Query database.
"""

import asyncio
import logging
import json
from typing import Union
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from .schema import Base, Citation, TagInstance, Time, Person, Place

log = logging.getLogger(__name__)

class Database:

    def __init__(self, config, stm_timeout: int=5):
        self._engine = create_engine(
            config.DB_URI,
            echo=config.DEBUG,
            future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.__short_term_memory = dict()
        self.__stm_timeout = stm_timeout

    def get_citations(self, citation_guids: list[str]) -> dict:
        """Expects a list of citation guids and returns their data in a dict 
        keyed by guid"""
        result = dict()
        with Session(self._engine, future=True) as session:
            for guid in citation_guids:
                res = session.execute(
                    select(Citation).where(Citation.guid==guid)
                ).scalar_one_or_none()
                if res:
                    result[guid] = {
                        'text': res.text,
                        'meta': json.loads(res.meta),
                        'tags': [self.get_tag_instance_data(t)
                                for t in res.tags]
                    }
                else:
                    result[guid] = {'error': 'citation guid does not exist'}
        return result

    def get_manifest_by_person(self, person_guid: str) -> list[str]:
        """Returns a list of given person's citations"""
        # should this include time tag as well?
        with Session(self._engine, future=True) as session:
            tags = session.execute(
                select(Person.tags).where(Person.guid == person_guid)
            )


    def create_citation(self,
        transaction_guid: str,
        citation_guid: str,
        text: str
        ) -> None:
        """Initializes a new citation in the database.
        Temporarily caches the new citation id for following operations."""
        c = Citation(
                guid=citation_guid,
                text=text)
        with Session(self._engine, future=True) as session:
            session.add(c)
            # save this id in memory for a few seconds
            session.commit()
            self.add_to_stm(
                key=transaction_guid,
                value=c.id)

    def handle_person_update(self,
        transaction_guid: str,
        person_guid: str,
        citation_guid: str,
        person_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool
        ) -> None:
        """Accepts the data from a person event and persists it to the database."""
        # since this is a primary entry point to the database,
        # get a session for the duration of this transaction
        with Session(self._engine, future=True) as session:
            # resolve person
            if is_new:
                person = Person(
                    guid=person_guid,
                    names=person_name)
            else:
                person = session.execute(
                    select(Person).where(Person.guid == person_guid)
                ).scalar_one()
                cur_names = self.split_names(person.names)
                if person_name not in cur_names:
                    person.names += f'|{person_name}'
            self._create_tag_instance(
                tag=person,
                transaction_guid=transaction_guid,
                citation_guid=citation_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session)
        
    def handle_place_update(self,
        transaction_guid: str,
        place_guid: str,
        citation_guid: str,
        place_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool,
        latitude: float=None,
        longitude: float=None,
        geoshape: str=None
        ) -> None:
        """Accepts the data from a place event and persists it to the database."""
        # since this is a primary entry point to the database,
        # get a session for the duration of this transaction
        with Session(self._engine, future=True) as session:
        # resolve place
            if is_new:
                place = Place(
                    guid=place_guid,
                    names=place_name,
                    latitude=latitude,
                    longitude=longitude,
                    geoshape=geoshape)
            else:
                place = session.execute(
                    select(Place).where(Place.guid == place_guid)
                ).scalar_one()
                cur_names = self.split_names(place.names)
                if place_name not in cur_names:
                    place.names += f'|{place_name}'
            self._create_tag_instance(
                tag=place,
                transaction_guid=transaction_guid,
                citation_guid=citation_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session)

    def handle_time_update(self,
        transaction_guid: str,
        time_guid: str,
        citation_guid: str,
        time_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool,
        ) -> None:
        """Accepts the data from a time event and persists it to the database"""
        # since this is a primary entry point to the database,
        # get a session for the duration of this transaction
        with Session(self._engine, future=True) as session:
            # resolve time
            if is_new:
                time = Time(
                    guid=time_guid,
                    name=time_name)
            else:
                time = session.execute(
                    select(Time).where(Time.guid == time_guid)
                ).scalar_one()
            self._create_tag_instance(
                tag=time,
                transaction_guid=transaction_guid,
                citation_guid=citation_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session)

    def _create_tag_instance(self, tag, transaction_guid, citation_guid,
        start_char, stop_char, session):
        """Second step of handle updates: creates a tag instance, and 
        associates it with citation and tag"""
        # resolve citation
        citation_id = self.__short_term_memory.get(transaction_guid)
        if not citation_id:
            citation_id = session.execute(
                select(Citation).where(Citation.guid == citation_guid)
            ).scalar_one().id
        # create Tag Instance
        tag_instance = TagInstance(
            citation_id=citation_id,
            tag=tag,
            start_char=start_char,
            stop_char=stop_char)
        session.add_all([tag, tag_instance])
        session.commit()

    def add_meta_to_citation(self, 
        citation_guid: str,
        **kwargs
        ) -> None:
        """Accepts meta data and associates it with a citation.
        
        Add all meta data as keyword arguments.
        """
        meta = json.dumps(kwargs)
        with Session(self._engine, future=True) as session:
            citation = session.execute(
                select(Citation).where(Citation.guid == citation_guid)
            ).scalar_one()
            citation.meta = meta
            session.commit()

    def add_to_stm(self, key, value):
        """Adds a value from an emitted event to the short term memory"""
        self.__short_term_memory[key] = value
        asyncio.create_task(self.__rm_from_stm(key))
        return
    
    async def __rm_from_stm(self, key):
        """internal method to clean up stale values from the stm"""
        await asyncio.sleep(self.__stm_timeout)
        del self.__short_term_memory[key]

    @staticmethod
    def split_names(names):
        return names.split('|')

    def get_tag_instance_data(self, tag_instance):
        """Accepts a TagInstance object and returns a dict representation"""
        res = {
                'start_char': tag_instance.start_char,
                'stop_char': tag_instance.stop_char,
                'tag_type': tag_instance.tag.type,
                'tag_guid': tag_instance.tag.guid
        }
        tag = tag_instance.tag
        if tag.type == 'TIME':
            res['name'] = tag.name
        elif tag.type == 'PLACE':
            res['names'] = self.split_names(tag.names)
            coords = {
                'latitude': tag.latitude,
                'longitude': tag.longitude
            }
            if tag.geoshape:
                coords['geoshape'] = tag.geoshape
            res['coords'] = coords
        elif tag.type == 'PERSON':
            res['names'] = self.split_names(tag.names)
        else:
            raise ValueError(f'Unknown tag type {tag.type}!')
        return res