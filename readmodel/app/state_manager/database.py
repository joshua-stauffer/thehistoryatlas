"""
SQLAlchemy integration for the History Atlas Read Model service.
Provides read and write access to the Query database.
"""

import asyncio
import logging
import json
from typing import Union
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from .schema import Base
from .schema import Citation
from .schema import History
from .schema import Name
from .schema import Person
from .schema import Place
from .schema import TagInstance
from .schema import Time
from .schema import Tag


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

    # QUERIES

    def get_citations(self, citation_guids: list[str]) -> list:
        """Expects a list of citation guids and returns their data in a dict 
        keyed by guid"""
        log.info(f'Received request to return {len(citation_guids)} Citations.')
        result = list()
        with Session(self._engine, future=True) as session:
            for guid in citation_guids:
                res = session.execute(
                    select(Citation).where(Citation.guid==guid)
                ).scalar_one_or_none()
                if res:
                    result.append({
                        'guid': guid,
                        'text': res.text,
                        'meta': json.loads(res.meta),
                        'tags': [self.get_tag_instance_data(t)
                                for t in res.tags]
                    })

        log.info(f'Returning {len(result)} Citations')
        return result

    def get_manifest_by_person(self,
        person_guid: str
        ) -> list[str]:
        """Returns a list of given person's citations"""
        return self.__get_manifest_util(
            entity_base=Person,
            guid=person_guid)

    def get_manifest_by_place(self,
        place_guid: str
        ) -> list[str]:
        """Returns a list of given place's citations"""
        return self.__get_manifest_util(
            entity_base=Place,
            guid=place_guid)

    def get_manifest_by_time(self,
        time_guid: str
        ) -> list[str]:
        """Returns a list of given place's citations"""
        return self.__get_manifest_util(
            entity_base=Time,
            guid=time_guid)

    def __get_manifest_util(self, entity_base, guid):
        """Utility to query db for manifest"""
        log.debug(f'Looking up manifest for GUID {guid}')
        with Session(self._engine, future=True) as session:
            entity = session.execute(
                select(entity_base).where(entity_base.guid==guid)
            ).scalar_one_or_none()
            if not entity:
                log.debug(f'Manifest lookup found nothing for GUID {guid}')
                return list()
            # DEBUG CODE:

            tag_instances = entity.tag_instances

            tag_list = [t for t in tag_instances]
            tag_list.sort(key=lambda a: a.citation.time_tag)
            result = [t.citation.guid for t in tag_instances]
        log.debug(f'Manifest lookup is returning a result of length {len(result)}')
        return result

    def get_guids_by_name(self, name) -> list[str]:
        """Allows searching on known names. Returns list of GUIDs, if any."""
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Name).where(Name.name==name)
            ).scalar_one_or_none()
            if not res:
                return list()
            return res.guids

    def get_entity_summary_by_guid_batch(self,
        guids: list[str]
        ) -> list[dict]:
        """Given a list of guids, find their type, name/alt names,
        first and last citation dates, and citation count, and returns
        a dict of the data keyed by guid."""
        res = list()
        with Session(self._engine, future=True) as session:
            for guid in guids:  
                entity = session.execute(
                    select(Tag).where(Tag.guid==guid)
                ).scalar_one_or_none()
                if not entity:
                    log.debug(f'Could not find entity {guid}')
                    continue
                # find names / account for TIME only having a single name
                if entity.type == 'TIME':
                    # TODO: when time is updated to allow for a range of two,
                    #       they ought to be treated the same as below
                    name_list = [entity.name]
                else:
                    name_list = self.split_names(entity.names)
                # get min/max of date range
                min_time = entity.tag_instances[0].citation.time_tag
                max_time = entity.tag_instances[0].citation.time_tag
                for tag in entity.tag_instances:
                    time = tag.citation.time_tag
                    if time < min_time:
                        min_time = time
                    if time > max_time:
                        max_time = time

                res.append({
                    'type': entity.type,
                    'guid': guid,
                    'citation_count': len(entity.tag_instances),
                    'names': name_list,
                    'first_citation_date': min_time,
                    'last_citation_date': max_time
                })
        return res

    # MUTATIONS

    def create_citation(self,
        transaction_guid: str,
        citation_guid: str,
        text: str
        ) -> None:
        """Initializes a new citation in the database.
        Temporarily caches the new citation id for following operations."""
        log.info(f'Creating a new citation: {text[:50]}...')
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
                log.info(f'Creating a new person: {person_name}')
                person = Person(
                    guid=person_guid,
                    names=person_name)
            else:
                log.info(f'Tagging an existing person: {person_name}')
                person = session.execute(
                    select(Person).where(Person.guid == person_guid)
                ).scalar_one()
                cur_names = self.split_names(person.names)
                if person_name not in cur_names:
                    person.names += f'|{person_name}'
            # add name to Name registry
            self._handle_name(person_name, person_guid, session)
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
            self._handle_name(place_name, place_guid, session)
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
            # cache timetag name on citation
            citation = session.execute(
                select(Citation).where(Citation.guid==citation_guid)
            ).scalar_one()
            citation.time_tag = time_name
            session.add(citation)
            self._handle_name(time_name, time_guid, session)
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
        log.debug('Creating a TagInstance')
        citation_id = self.__short_term_memory.get(transaction_guid)
        if not citation_id:
            log.debug('Couldn\'t find citation id in short term memory: ' + \
                      'looking it up')
            citation_id = session.execute(
                select(Citation).where(Citation.guid == citation_guid)
            ).scalar_one().id
        log.debug(f'Citation ID is {citation_id}')
        # create Tag Instance
        tag_instance = TagInstance(
            citation_id=citation_id,
            tag=tag,
            start_char=start_char,
            stop_char=stop_char)
        
        session.add_all([tag, tag_instance])
        session.commit()
        log.debug('☀️ ☀️ ☀️ Created tag instance and tag. ' + \
                 f'TagInstance id is {tag_instance.id}, ' + \
                 f'TagInstance Citation ID is {tag_instance.citation_id}, ' + \
                 f'TagInstance Tag ID is {tag_instance.tag_id}')

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

    def _handle_name(self, name, guid, session):
        """Accepts a name and GUID and links the two in the Name table"""
        res = session.execute(
            select(Name).where(Name.name==name)
        ).scalar_one_or_none()
        if not res:
            res = Name(
                name=name,
                guids=guid)
        else:
            # check if guid is already represented
            if guid in res.guids:
                return
            res.add_guid(guid)
        session.add(res)

    # HISTORY MANAGEMENT

    def check_database_init(self) -> int:
        """Checks database for the most recent event id. Returns None if 
        database isn't initialized yet, otherwise most recent id."""
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(History)
            ).scalar_one_or_none()
            if not res:
                # initialize with default row
                session.add(History())
                session.commit()
                return 0
            return res.latest_event_id

    def update_last_event_id(self, event_id: int) -> int:
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(History)
            ).scalar_one_or_none()
            if not res:
                res = History(latest_event_id=event_id)
            # for now, not checking if id is out of order
            res.latest_event_id = event_id
            session.add(res)
            session.commit()

    # UTILITY

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
