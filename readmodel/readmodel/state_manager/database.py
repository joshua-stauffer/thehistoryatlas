"""
SQLAlchemy integration for the History Atlas Read Model service.
Provides read and write access to the Query database.
"""

import asyncio
import logging
from dataclasses import asdict
from time import sleep
from typing import Tuple, Union, Literal, Optional, List, Dict

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from abstract_domain_model.models.readmodel import DefaultEntity, Source as ADMSource
from readmodel.state_manager.schema import (
    Base,
    Citation,
    History,
    Name,
    Person,
    Place,
    Summary,
    Tag,
    TagInstance,
    Time,
    Source,
)
from readmodel.state_manager.trie import Trie, TrieResult

log = logging.getLogger(__name__)


class Database:
    def __init__(self, config, stm_timeout: int = 5):
        self._engine = self._connect(
            uri=config.DB_URI, debug=config.DEBUG, retries=-1, timeout=1  # infinite
        )
        # initialize the db
        Base.metadata.create_all(self._engine)
        self.__short_term_memory = dict()
        self.__stm_timeout = stm_timeout
        # intialize the search trie
        self._entity_trie = Trie(self.get_all_entity_names())
        self._source_trie = Trie(self.get_all_source_titles_and_authors())

    def _connect(self, uri: str, debug: bool, retries: int = -1, timeout=30):

        while True:
            # while retries != 0:  # negative number allows infinite retries
            try:
                eng = create_engine(uri, echo=debug, echo_pool=True, future=True)
                return eng
            except BaseException:
                print(f"hit exception {e}")
                retries -= 1
                sleep(timeout)

        raise Exception("Exceeded max retries -- cannot connect to database.")

    # QUERIES

    def get_citation(self, citation_guid: str) -> dict:
        """Resolves citation GUID to its value in the database"""
        # NOTE: refactored as part of resolving issue 11 on 6.14.21
        #       previously known as get_citations, and returned a list
        log.debug(f"Looking up citation for citation GUID {citation_guid}")
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Citation).where(Citation.guid == citation_guid)
            ).scalar_one_or_none()
            if res:
                return {
                    "guid": citation_guid,
                    "text": res.text,
                    "meta": {"accessDate": res.access_date, "pageNum": res.page_num},
                    "source_id": res.source_id,
                }
            else:
                log.debug(f"Found no citation for citation GUID {citation_guid}")
                return {}

    def get_summaries(self, summary_guids: list[str]) -> list[dict]:
        """Expects a list of summary guids and returns their data in a dict
        keyed by guid"""
        log.debug(f"Received request to return {len(summary_guids)} summaries.")
        result = list()
        with Session(self._engine, future=True) as session:
            for guid in summary_guids:
                res = session.execute(
                    select(Summary).where(Summary.guid == guid)
                ).scalar_one_or_none()
                if res:
                    result.append(
                        {
                            "guid": guid,
                            "text": res.text,
                            "tags": [self.get_tag_instance_data(t) for t in res.tags],
                            "citation_guids": [r.guid for r in res.citations],
                        }
                    )
        log.debug(f"Returning {len(result)} summaries")
        return result

    def get_manifest_by_person(self, person_guid: str) -> list[str]:
        """Returns a list of given person's citations"""
        return self._get_manifest_util(entity_base=Person, guid=person_guid)

    def get_manifest_by_place(self, place_guid: str) -> list[str]:
        """Returns a list of given place's citations"""
        return self._get_manifest_util(entity_base=Place, guid=place_guid)

    def get_manifest_by_time(self, time_guid: str) -> list[str]:
        """Returns a list of given place's citations"""
        return self._get_manifest_util(entity_base=Time, guid=time_guid)

    def _get_manifest_util(
        self, entity_base, guid
    ) -> tuple[list[str], dict[int, dict[str, Union[str, int]]]]:
        """Utility to query db for manifest -- also calculates timeline summary."""
        log.debug(f"Looking up manifest for GUID {guid}")
        with Session(self._engine, future=True) as session:
            entity = session.execute(
                select(entity_base).where(entity_base.guid == guid)
            ).scalar_one_or_none()
            if not entity:
                log.debug(f"Manifest lookup found nothing for GUID {guid}")
                return list()

            tag_instances = entity.tag_instances

            tag_list = [t for t in tag_instances]
            # TODO: update this to better handle multiple time tags
            tag_list.sort(key=lambda a: a.summary.time_tag)
            tag_result = list()
            timeline_dict = dict()
            for tag in tag_list:
                tag_result.append(tag.summary.guid)
                year = self.get_year_from_date(tag.summary.time_tag)
                if time_res := timeline_dict.get(year):
                    time_res["count"] += 1
                else:
                    timeline_dict[year] = {"count": 1, "root_guid": tag.summary.guid}
        timeline_result = [
            {
                "year": year,
                "count": timeline_dict[year]["count"],
                "root_guid": timeline_dict[year]["root_guid"],
            }
            for year in timeline_dict.keys()
        ]
        return tag_result, timeline_result

    def get_guids_by_name(self, name) -> list[str]:
        """Allows searching on known names. Returns list of GUIDs, if any."""
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Name).where(Name.name == name)
            ).scalar_one_or_none()
            if not res:
                return list()
            return res.guids

    def get_entity_summary_by_guid_batch(self, guids: list[str]) -> list[dict]:
        """Given a list of guids, find their type, name/alt names,
        first and last citation dates, and citation count, and returns
        a dict of the data keyed by guid."""
        res = list()
        with Session(self._engine, future=True) as session:
            for guid in guids:
                entity = session.execute(
                    select(Tag).where(Tag.guid == guid)
                ).scalar_one_or_none()
                if not entity:
                    log.debug(f"Could not find entity {guid}")
                    continue
                # find names / account for TIME only having a single name
                if entity.type == "TIME":
                    # TODO: when time is updated to allow for a range of two,
                    #       they ought to be treated the same as below
                    name_list = [entity.name]
                else:
                    name_list = self.split_names(entity.names)
                # get min/max of date range
                min_time = entity.tag_instances[0].summary.time_tag
                max_time = entity.tag_instances[0].summary.time_tag
                for tag in entity.tag_instances:
                    time = tag.summary.time_tag
                    if time < min_time:
                        min_time = time
                    if time > max_time:
                        max_time = time

                res.append(
                    {
                        "type": entity.type,
                        "guid": guid,
                        "citation_count": len(entity.tag_instances),
                        "names": name_list,
                        "first_citation_date": min_time,
                        "last_citation_date": max_time,
                    }
                )
        return res

    def get_all_entity_names(self) -> List[Tuple[str, str]]:
        """Util for building Entity search trie. Returns a list of (name, guid) tuples."""
        res = []
        with Session(self._engine, future=True) as session:

            people = session.execute(select(Person)).scalars()
            for person in people:
                for name in person.names.split("|"):
                    res.append((name, person.guid))

            places = session.execute(select(Place)).scalars()
            for place in places:
                for name in place.names.split("|"):
                    res.append((name, place.guid))

            times = session.execute(select(Time)).scalars()
            for time in times:
                res.append((time.name, time.guid))

        return res

    def get_all_source_titles_and_authors(self) -> List[Tuple[str, str]]:
        """Util for building Source search trie. Returns a list of (name, id) tuples."""
        res: List[Tuple[str, str]] = []
        with Session(self._engine, future=True) as session:
            sources = session.query(Source).all()
            for source in sources:
                res.extend(
                    [
                        (source.title, source.id),
                        (source.author, source.id),
                    ]
                )
        return res

    def get_name_by_fuzzy_search(self, name: str) -> List[Dict]:
        """Search for possible completions to a given string from known entity names."""
        if name == "":
            return []
        return [
            asdict(trie_result)
            for trie_result in self._entity_trie.find(name, res_count=10)
        ]

    def get_sources_by_search_term(self, search_term: str) -> list[ADMSource]:
        """Match a list of Sources by title and author against a search term."""
        if search_term == "":
            return []
        res: List[ADMSource] = []
        source_results = self._source_trie.find(search_term, res_count=10)
        source_ids = set([id for source in source_results for id in source.guids])
        with Session(self._engine, future=True) as session:
            for source_id in source_ids:
                source = session.query(Source).filter(Source.id == source_id).one()
                res.append(
                    ADMSource(
                        id=source_id,
                        title=source.title,
                        author=source.author,
                        publisher=source.publisher,
                        pub_date=source.pub_date,
                    )
                )
        return res

    def get_place_by_coords(
        self, latitude: float, longitude: float
    ) -> Union[str, None]:
        """Search for a place by latitude or longitude and receive a GUID in return"""

        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Place)
                .where(Place.latitude == latitude)
                .where(Place.longitude == longitude)
            ).scalar_one_or_none()

            if res:
                return res.guid
            return None

    def get_default_entity(self) -> DefaultEntity:
        """
        Get a default starting entity
        """
        # always start with a place
        with Session(self._engine, future=True) as session:
            tag = session.execute(
                select(Place).order_by(func.random()).limit(1)
            ).scalar_one_or_none()
            if tag is None:
                raise Exception(
                    "Database must have at least one entity -- add a new citation, and try again."
                )

            return DefaultEntity(id=tag.guid, name=tag.names, type="PLACE")

    # MUTATIONS

    def create_summary(self, summary_guid: str, text: str) -> None:
        """Creates a new summary, and caches its database level id for any
        following operations to use"""
        log.info(f"Creating a new summary: {text[:50]}...")
        summary = Summary(guid=summary_guid, text=text)
        with Session(self._engine, future=True) as session:
            session.add(summary)
            session.commit()
            self.add_to_stm(key=summary_guid, value=summary.id)

    def create_citation(
        self,
        citation_guid: str,
        summary_guid: str,
        text: str,
        page_num: Optional[int] = None,
        access_date: Optional[str] = None,
    ) -> None:
        """Initializes a new citation in the database."""

        log.info(f"Creating a new citation: {text[:50]}...")
        summary_id = self.get_summary_id(summary_guid=summary_guid)
        c = Citation(
            guid=citation_guid,
            text=text,
            summary_id=summary_id,
            page_num=page_num,
            access_date=access_date,
        )
        with Session(self._engine, future=True) as session:
            session.add(c)
            session.commit()

    def handle_person_update(
        self,
        person_guid: str,
        summary_guid: str,
        person_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool,
    ) -> None:
        """Accepts the data from a person event and persists it to the database."""
        # since this is a primary entry point to the database,
        # get a session for the duration of this transaction
        with Session(self._engine, future=True) as session:
            # resolve person
            if is_new:
                log.debug(f"Creating a new person: {person_name}")
                person = Person(guid=person_guid, names=person_name)
            else:
                log.debug(f"Tagging an existing person: {person_name}")
                person = session.execute(
                    select(Person).where(Person.guid == person_guid)
                ).scalar_one()
                cur_names = self.split_names(person.names)
                if person_name not in cur_names:
                    log.debug(f"found new person name {person_name}")
                    person.names += f"|{person_name}"
                    log.debug(f"person.names is now {person.names}")
            # add name to Name registry
            self._handle_name(person_name, person_guid, session)
            self._create_tag_instance(
                tag=person,
                summary_guid=summary_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )

    def handle_place_update(
        self,
        place_guid: str,
        summary_guid: str,
        place_name: str,
        start_char: int,
        stop_char: int,
        is_new: bool,
        latitude: float = None,
        longitude: float = None,
        geoshape: str = None,
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
                    geoshape=geoshape,
                )
            else:
                place = session.execute(
                    select(Place).where(Place.guid == place_guid)
                ).scalar_one()
                cur_names = self.split_names(place.names)
                if place_name not in cur_names:
                    place.names += f"|{place_name}"
            self._handle_name(place_name, place_guid, session)
            self._create_tag_instance(
                tag=place,
                summary_guid=summary_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )

    def handle_time_update(
        self,
        time_guid: str,
        summary_guid: str,
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
                time = Time(guid=time_guid, name=time_name)
            else:
                time = session.execute(
                    select(Time).where(Time.guid == time_guid)
                ).scalar_one()
            # cache timetag name on summary
            # NOTE: this currently results in a 'last write wins' scenario
            summary = session.execute(
                select(Summary).where(Summary.guid == summary_guid)
            ).scalar_one()
            summary.time_tag = time_name
            session.add(summary)
            self._handle_name(time_name, time_guid, session)
            self._create_tag_instance(
                tag=time,
                summary_guid=summary_guid,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )

    def _create_tag_instance(
        self,
        tag: Tag,
        summary_guid: str,
        start_char: int,
        stop_char: int,
        session: Session,
    ):
        """Second: step of handle updates: creates a tag instance, and
        associates it with citation and tag"""
        # resolve citation
        log.debug("Creating a TagInstance")
        summary_id = self.get_summary_id(summary_guid=summary_guid, session=session)

        # create Tag Instance
        tag_instance = TagInstance(
            summary_id=summary_id, tag=tag, start_char=start_char, stop_char=stop_char
        )

        session.add_all([tag, tag_instance])
        session.commit()
        print("just committed the session: ", tag)
        log.debug(
            "☀️ ☀️ ☀️ Created tag instance and tag. "
            + f"TagInstance id is {tag_instance.id}, "
            + f"TagInstance Summary ID is {tag_instance.summary_id}, "
            + f"TagInstance Tag ID is {tag_instance.tag_id}"
        )

    def add_source_to_citation(self, source_id: str, citation_id: str) -> None:
        """
        Associate an existing Source with a Citation.
        """
        with Session(self._engine, future=True) as session:
            citation = session.execute(
                select(Citation).where(Citation.guid == citation_id)
            ).scalar_one()
            citation.source_id = source_id
            session.commit()

    def create_source(
        self,
        id: str,
        title: str,
        author: str,
        publisher: str,
        pub_date: str,
        citation_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Create a new Source record, and optionally associate it with a Citation.
        """
        with Session(self._engine, future=True) as session:
            source = Source(
                id=id,
                title=title,
                author=author,
                publisher=publisher,
                pub_date=pub_date,
                kwargs=kwargs,
            )
            session.add(source)

            if citation_id is not None:
                citation = session.execute(
                    select(Citation).where(Citation.guid == citation_id)
                ).scalar_one()
                citation.source_id = id
                session.add(citation)
            session.commit()
            self._add_to_source_trie(source)

    def _add_to_source_trie(self, source: Source):
        """
        Add source title and author to the search trie,
        as well as their individual words.
        """
        id = source.id

        # add title
        self._source_trie.insert(source.title, guid=id)
        title_words = source.title.split(" ")
        if len(title_words) > 1:
            for word in title_words:
                self._source_trie.insert(word, guid=id)

        # add author
        self._source_trie.insert(source.author, guid=id)
        author_words = source.title.split(" ")
        if len(author_words) > 1:
            for word in author_words:
                self._source_trie.insert(word, guid=id)

    def _handle_name(self, name, guid, session):
        """Accepts a name and GUID and links the two in the Name table and
        updates the name search trie."""
        res = session.execute(
            select(Name).where(Name.name == name)
        ).scalar_one_or_none()
        if not res:
            res = Name(name=name, guids=guid)
            self.update_entity_trie(new_string=name, new_string_guid=guid)
        else:
            # check if guid is already represented
            if guid in res.guids:
                return  # this name/guid pair isn't new
            res.add_guid(guid)
            self.update_entity_trie(new_string=name, new_string_guid=guid)
        session.add(res)

    # CACHE LAYER FOR INCOMING CITATIONS

    def get_summary_id(self, summary_guid: str, session=None) -> int:
        """fetches a summary id, utilizing caching if possible."""
        if id := self.__short_term_memory.get(summary_guid):
            return id
        if not session:
            with Session(self._engine, future=True) as session:
                res = session.execute(
                    select(Summary).where(Summary.guid == summary_guid)
                ).scalar_one()
                # cache result
                self.add_to_stm(key=summary_guid, value=res.id)
                return res.id
        else:
            res = session.execute(
                select(Summary).where(Summary.guid == summary_guid)
            ).scalar_one()
            # cache result
            self.add_to_stm(key=summary_guid, value=res.id)
            return res.id

    # HISTORY MANAGEMENT

    def check_database_init(self) -> int:
        """Checks database for the most recent event id. Returns None if
        database isn't initialized yet, otherwise most recent id."""
        with Session(self._engine, future=True) as session:
            res = session.execute(select(History)).scalar_one_or_none()
            if not res:
                # initialize with default row
                session.add(History())
                session.commit()
                return 0
            return res.latest_event_id

    def update_last_event_id(self, event_id: int) -> int:
        with Session(self._engine, future=True) as session:
            res = session.execute(select(History)).scalar_one_or_none()
            if not res:
                res = History(latest_event_id=event_id)
            # for now, not checking if id is out of order
            res.latest_event_id = event_id
            session.add(res)
            session.commit()

    # TRIE MANAGEMENT

    def update_entity_trie(
        self,
        new_string=None,
        new_string_guid=None,
        old_string=None,
        old_string_guid=None,
    ):
        """
        Maintains trie state by adding new string and/or removing old string.
        if new_string is provided, new_string_guid is required as well.
        if old_string is provided, old_string_guid is required as well.
        """
        if new_string:
            if not new_string_guid:
                raise Exception(
                    f"Update_trie was provided with new_string {new_string} but not a new_string_guid."
                )
            self._entity_trie.insert(string=new_string, guid=new_string_guid)
        if old_string:
            if not new_string_guid:
                raise Exception(
                    f"Update_trie was provided with old_string {new_string} but not a new_string_guid."
                )
            self._entity_trie.delete(string=old_string, guid=old_string_guid)

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
        return names.split("|")

    def get_tag_instance_data(self, tag_instance):
        """Accepts a TagInstance object and returns a dict representation"""
        res = {
            "start_char": tag_instance.start_char,
            "stop_char": tag_instance.stop_char,
            "tag_type": tag_instance.tag.type,
            "tag_guid": tag_instance.tag.guid,
        }
        tag = tag_instance.tag
        if tag.type == "TIME":
            res["name"] = tag.name
        elif tag.type == "PLACE":
            res["names"] = self.split_names(tag.names)
            coords = {"latitude": tag.latitude, "longitude": tag.longitude}
            if tag.geoshape:
                coords["geoshape"] = tag.geoshape
            res["coords"] = coords
        elif tag.type == "PERSON":
            res["names"] = self.split_names(tag.names)
        else:
            raise ValueError(f"Unknown tag type {tag.type}!")
        return res

    def get_year_from_date(self, date) -> int:
        split_date = date.split("|")
        return int(split_date[0])
