import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Tuple, Union, Optional, List, Dict
from uuid import uuid4, UUID

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session, sessionmaker

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.readmodel import (
    DefaultEntity,
    Source as ADMSource,
)
from the_history_atlas.apps.domain.models.readmodel.queries import FuzzySearchByName
from the_history_atlas.apps.domain.models.readmodel.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TagNameAssocModel,
    CitationModel,
)
from the_history_atlas.apps.domain.models.readmodel.tables.time import (
    TimePrecision,
    TimeModel,
)
from the_history_atlas.apps.readmodel.errors import MissingResourceError
from the_history_atlas.apps.readmodel.schema import (
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
from the_history_atlas.apps.readmodel.trie import Trie

log = logging.getLogger(__name__)


class Database:

    Session: sessionmaker

    def __init__(self, database_client: DatabaseClient):
        self._engine = database_client
        self.Session = sessionmaker(bind=database_client)
        # initialize the db
        Base.metadata.create_all(self._engine)
        # intialize the search trie
        self._entity_trie = Trie(self.get_all_entity_names())
        self._source_trie = Trie(self.get_all_source_titles_and_authors())

    def get_citation(self, citation_guid: str) -> dict:
        """Resolves citation GUID to its value in the database"""
        log.debug(f"Looking up citation for citation GUID {citation_guid}")
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Citation).where(Citation.id == citation_guid)
            ).scalar_one_or_none()
            if res:
                return {
                    "id": citation_guid,
                    "text": res.text,
                    "meta": {"accessDate": res.access_date, "pageNum": res.page_num},
                    "source_id": res.source_id,
                }
            else:
                log.debug(f"Found no citation for citation GUID {citation_guid}")
                return {}

    def get_citation_by_id(self, id: UUID, session: Session) -> CitationModel | None:
        stmt = """
            select id, text, source_id, summary_id, page_num, access_date
            from citations where citations.id = :id
        """
        output = session.execute(text(stmt), {"id": id}).one_or_none()
        if output is None:
            return output
        (id, citation_text, source_id, summary_id, page_num, access_date) = output
        return CitationModel(
            id=id,
            text=citation_text,
            source_id=source_id,
            summary_id=summary_id,
            page_num=page_num,
            access_date=access_date,
        )

    def get_summaries(self, summary_guids: list[str]) -> list[dict]:
        """Expects a list of summary guids and returns their data in a dict
        keyed by guid"""
        log.debug(f"Received request to return {len(summary_guids)} summaries.")
        result = list()
        with Session(self._engine, future=True) as session:
            for guid in summary_guids:
                res = session.execute(
                    select(Summary).where(Summary.id == guid)
                ).scalar_one_or_none()
                if res:
                    result.append(
                        {
                            "guid": guid,
                            "text": res.text,
                            "tags": [self.get_tag_instance_data(t) for t in res.tags],
                            "citation_ids": [r.guid for r in res.citations],
                        }
                    )
        log.debug(f"Returning {len(result)} summaries")
        return result

    def get_manifest_by_person(self, person_guid: str) -> tuple[list, list]:
        """Returns a list of given person's citations"""
        return self._get_manifest_util(entity_base=Person, guid=person_guid)

    def get_manifest_by_place(self, place_guid: str) -> tuple[list, list]:
        """Returns a list of given place's citations"""
        return self._get_manifest_util(entity_base=Place, guid=place_guid)

    def get_manifest_by_time(self, time_guid: str) -> tuple[list, list]:
        """Returns a list of given place's citations"""
        return self._get_manifest_util(entity_base=Time, guid=time_guid)

    def _get_manifest_util(self, entity_base, guid) -> tuple[list, list]:
        """Utility to query db for manifest -- also calculates timeline summary."""
        log.debug(f"Looking up manifest for GUID {guid}")
        with Session(self._engine, future=True) as session:
            entity = session.execute(
                select(entity_base).where(entity_base.id == guid)
            ).scalar_one_or_none()
            if not entity:
                log.debug(f"Manifest lookup found nothing for GUID {guid}")
                return [], []

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
                "root_id": timeline_dict[year]["root_guid"],
            }
            for year in timeline_dict.keys()
        ]
        return tag_result, timeline_result

    def get_guids_by_name(self, name: str) -> list[UUID]:
        """Allows searching on known names. Returns list of GUIDs, if any."""
        with Session(self._engine, future=True) as session:
            res = session.execute(
                select(Name).where(Name.name == name)
            ).scalar_one_or_none()
            if not res:
                return list()
            return [tag.id for tag in res.tags]

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
                        "id": guid,
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
                for name in person.names:
                    res.append((name.name, person.id))

            places = session.execute(select(Place)).scalars()
            for place in places:
                for name in place.names:
                    res.append((name.name, place.id))

            times = session.execute(select(Time)).scalars()
            for time in times:
                for name in time.names:
                    res.append((name.name, time.id))

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

    def get_name_by_fuzzy_search(self, name: str) -> List[FuzzySearchByName]:
        """Search for possible completions to a given string from known entity names."""
        if name == "":
            return []
        return [
            FuzzySearchByName(name=trie_result.name, ids=trie_result.guids)
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

    def get_coords_by_names(self, names: list[str]) -> CoordsByName:
        with Session(self._engine, future=True) as session:
            sql = """
                select from places names, latitude, longitude
                
            """

    # MUTATIONS

    def create_summary(self, id: UUID, text: str) -> None:
        """Creates a new summary"""
        log.info(f"Creating a new summary: {text[:50]}...")
        summary = Summary(id=id, text=text)
        with Session(self._engine, future=True) as session:
            session.add(summary)
            session.commit()

    def create_citation(
        self,
        session: Session,
        id: UUID,
        citation_text: str,
        page_num: Optional[int] = None,
        access_date: Optional[str] = None,
    ) -> None:
        """Initializes a new citation in the database."""
        # doesn't create fkeys
        stmt = """
            insert into citations (id, text, page_num, access_date)
            values (:id, :text, :page_num, :access_date)
        """
        session.execute(
            text(stmt),
            {
                "id": id,
                "text": citation_text,
                "page_num": page_num,
                "access_date": access_date,
            },
        )

    def create_citation_source_fkey(
        self,
        session: Session,
        citation_id: UUID,
        source_id: UUID,
    ):
        stmt = f"""
            update citations set source_id = :source_id 
                where citations.id = :citation_id
        """
        session.execute(
            text(stmt), {"source_id": source_id, "citation_id": citation_id}
        )

    def create_citation_summary_fkey(
        self,
        session: Session,
        citation_id: UUID,
        summary_id: UUID,
    ):
        stmt = f"""
            update citations set summary_id = :summary_id 
                where citations.id = :citation_id
        """
        session.execute(
            text(stmt), {"summary_id": summary_id, "citation_id": citation_id}
        )

    def get_person_by_id(self, id: UUID, session: Session) -> PersonModel | None:
        stmt = """
            select (id)
            from person where person.id = :id;
        """
        person_id = session.execute(text(stmt), {"id": id}).scalar_one_or_none()
        if person_id is None:
            return None
        return PersonModel(id=person_id)

    def create_person(self, id: UUID, session: Session) -> PersonModel:
        stmt = """
                insert into tags (id, type)
                values (:id, :type);
                insert into person (id)
                values (:id);
            """
        session.execute(text(stmt), {"id": id, "type": "PERSON"})
        return PersonModel(id=id)

    def get_place_by_id(self, id: UUID, session: Session) -> PlaceModel | None:
        stmt = """
            select id, latitude, longitude, geoshape, geonames_id
            from place where place.id = :id;
        """
        res = session.execute(text(stmt), {"id": id}).one_or_none()
        if res is None:
            return None
        return PlaceModel(
            id=res[0],
            latitude=res[1],
            longitude=res[2],
            geoshape=res[3],
            geonames_id=res[4],
        )

    def create_place(
        self,
        session: Session,
        id: UUID,
        latitude: float | None = None,
        longitude: float | None = None,
        geoshape: str | None = None,
        geonames_id: int | None = None,
    ) -> PlaceModel:
        place_model = PlaceModel(
            id=id,
            latitude=latitude,
            longitude=longitude,
            geoshape=geoshape,
            geonames_id=geonames_id,
        )
        insert_place = """
            insert into tags (id, type)
                values (:id, :type);
            insert into place (id, latitude, longitude, geoshape, geonames_id)
                values (:id, :latitude, :longitude, :geoshape, :geonames_id)
        """
        session.execute(text(insert_place), place_model.dict())
        return place_model

    def get_time_by_id(self, id: UUID, session: Session) -> TimeModel | None:
        stmt = """
            select id, time, calendar_model, precision
            from time where time.id = :id;
        """
        res = session.execute(text(stmt), {"id": id}).one_or_none()
        if res is None:
            return None
        return TimeModel(
            id=res[0],
            time=res[1],
            calendar_model=res[2],
            precision=res[3],
        )

    def create_time(
        self,
        session: Session,
        id: UUID,
        time: datetime,
        calendar_model: str,
        precision: TimePrecision,
    ):
        time_model = TimeModel(
            id=id, time=time, calendar_model=calendar_model, precision=precision
        )
        insert_time = """
            insert into tags (id, type)
                values (:id, :type);
            insert into time (id, time, calendar_model, precision)
                values (:id, :time, :calendar_model, :precision);
        """
        session.execute(text(insert_time), time_model.dict())
        return time_model

    def create_name(self, name: str, session: Session) -> NameModel:
        id = uuid4()
        insert_name = """
            insert into names (id, name)
                values (:id, :name);
        """
        session.execute(text(insert_name), {"id": id, "name": name})
        return NameModel(id=id, name=name)

    def get_name(self, name: str, session: Session) -> NameModel | None:
        get_name = """
            select id from names where names.name = :name;
        """
        name_id = session.execute(text(get_name), {"name": name}).scalar_one_or_none()
        if name_id is not None:
            return NameModel(id=name_id, name=name)
        else:
            return None

    def create_tag_instance(
        self,
        start_char: int,
        stop_char: int,
        summary_id: UUID,
        tag_id: UUID,
        session: Session,
    ) -> TagInstanceModel:
        id = uuid4()
        tag_instance = TagInstanceModel(
            id=id,
            start_char=start_char,
            stop_char=stop_char,
            summary_id=summary_id,
            tag_id=tag_id,
        )
        stmt = """
            insert into taginstances
                (id, start_char, stop_char, summary_id, tag_id)
            values
                (:id, :start_char, :stop_char, :summary_id, :tag_id)        
        """
        session.execute(text(stmt), tag_instance.dict())
        return tag_instance

    def exists_tag(self, tag_id: UUID, session: Session) -> bool:
        get_tag = "select id from tags where tags.id = :tag_id"
        tag_id = session.execute(text(get_tag), {"tag_id": tag_id}).scalar_one_or_none()
        return tag_id is not None

    def add_name_to_tag(
        self, session: Session, tag_id: UUID, name: str, lang: str | None = None
    ):
        """Ensure name exists, and associate it with the tag."""
        # todo: handle lang
        name_model = self.get_name(name=name, session=session)
        if name_model is None:
            name_model = self.create_name(name=name, session=session)

        tag_name_assoc = TagNameAssocModel(name_id=name_model.id, tag_id=tag_id)

        stmt = """
            insert into tag_name_assoc (tag_id, name_id)
                values (:tag_id, :name_id);
        """
        session.execute(text(stmt), tag_name_assoc.dict())

    def add_source_to_citation(self, source_id: UUID, citation_id: UUID) -> None:
        """
        Associate an existing Source with a Citation.
        """
        with Session(self._engine, future=True) as session:
            citation = session.execute(
                select(Citation).where(Citation.id == citation_id)
            ).scalar_one()
            citation.source_id = source_id
            session.commit()

    def create_source(
        self,
        id: UUID,
        title: str,
        author: str,
        publisher: str,
        pub_date: str,
        citation_id: Optional[UUID] = None,
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
                self.create_citation_source_fkey(
                    source_id=id, citation_id=citation_id, session=session
                )
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
                    f"Update_trie was provided with old_string {old_string} but not a new_string_guid."
                )
            self._entity_trie.delete(string=old_string, guid=old_string_guid)

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
