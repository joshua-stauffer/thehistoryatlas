import logging
from collections import defaultdict
from datetime import datetime
from typing import Tuple, Union, Optional, List, Literal
from uuid import uuid4, UUID

from sqlalchemy import select, func, text
from sqlalchemy.engine import row
from sqlalchemy.orm import Session, sessionmaker

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.core import (
    TagPointer,
    StoryOrder,
    StoryName,
    StoryPointer,
)
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.readmodel import (
    DefaultEntity,
    Source as ADMSource,
)
from the_history_atlas.apps.domain.models.readmodel.queries import FuzzySearchByName
from the_history_atlas.apps.domain.models.readmodel.queries.coords_by_name import Coords
from the_history_atlas.apps.domain.models.readmodel.queries.get_events import (
    EventQuery,
    EventRow,
    TagRow,
    CalendarDateRow,
    LocationRow,
    TagNames,
)
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
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.readmodel.schema import (
    Base,
    Citation,
    Name,
    Person,
    Place,
    Summary,
    Tag,
    Time,
    Source,
)
from the_history_atlas.apps.readmodel.trie import Trie, TrieResult

log = logging.getLogger(__name__)


class Database:

    Session: sessionmaker

    def __init__(
        self, database_client: DatabaseClient, source_trie: Trie, entity_trie: Trie
    ):
        self._entity_trie = source_trie
        self._source_trie = entity_trie
        self._engine = database_client

        self.Session = sessionmaker(bind=database_client)
        Base.metadata.create_all(self._engine)

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
                tag_result.append(tag.summary.id)
                year = self.get_year_from_date(tag.summary.time_tag)
                if time_res := timeline_dict.get(year):
                    time_res["count"] += 1
                else:
                    timeline_dict[year] = {"count": 1, "root_guid": tag.summary.id}
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
                    select(Tag).where(Tag.id == guid)
                ).scalar_one_or_none()
                if entity is None or not entity.tag_instances:
                    log.debug(f"Could not find entity {guid}")
                    continue
                names = [name.name for name in entity.names]

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
                        "names": names,
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
            FuzzySearchByName(
                name=trie_result.name, ids=[UUID(id) for id in trie_result.guids]
            )
            for trie_result in self._entity_trie.find(name, res_count=10)
        ]

    def get_sources_by_search_term(self, sources: list[TrieResult]) -> list[ADMSource]:
        """Match a list of Sources by title and author against a search term."""
        res: List[ADMSource] = []
        source_ids = set([id for source in sources for id in source.ids])
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
                return res.id
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

            return DefaultEntity(id=tag.id, name=tag.names, type="PLACE")

    def get_default_story_and_event(
        self,
    ) -> StoryPointer:
        with Session(self._engine, future=True) as session:
            # get the beginning of a person's life
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM taginstances
                    JOIN tags ON taginstances.tag_id = tags.id
                    WHERE taginstances.story_order = 0
                    AND tags.type = 'PERSON'
                    ORDER BY RANDOM()
                    LIMIT 1;
                """
                )
            ).one()
            return StoryPointer(
                event_id=row.event_id,
                story_id=row.story_id,
            )

    def get_default_event_by_story(self, story_id: UUID) -> StoryPointer:
        # todo
        return self.get_default_story_and_event()

    def get_default_story_by_event(self, event_id: UUID) -> StoryPointer:
        # todo
        return self.get_default_story_and_event()

    def get_story_pointers(
        self,
        summary_id: UUID,
        tag_id: UUID,
        direction: Literal["next", "prev"] | None,
        session: Session,
    ) -> List[StoryPointer]:
        match direction:
            case "next":
                operator = ">="
                predicate = ""
            case "prev":
                operator = "<="
                predicate = ""
            case None:
                operator = ">="
                predicate = "- 5"
            case _:
                raise RuntimeError("Unknown direction")
        query = f"""
                select 
                    ti.summary_id as event_id,
                    ti.tag_id as story_id
                from taginstances ti
                where ti.tag_id = :tag_id
                and ti.story_order {operator} (
                    select story_order from taginstances
                    where taginstances.tag_id =  :tag_id
                    and taginstances.summary_id = :summary_id
                ) {predicate}
                order by ti.story_order
                limit 10
            """
        rows = session.execute(
            text(query), {"tag_id": tag_id, "summary_id": summary_id}
        ).all()
        return [StoryPointer.model_validate(row, from_attributes=True) for row in rows]

    def get_events(
        self, event_ids: tuple[UUID, ...], session: Session
    ) -> list[EventQuery]:
        event_query = session.execute(
            text(
                """
                -- event_rows
                select 
                    summaries.id as event_id,
                    summaries.text as text,
                    sources.id as source_id,
                    citations.text as source_text,
                    sources.title as source_title,
                    sources.author as source_author,
                    sources.publisher as source_publisher,
                    citations.access_date as source_access_date
                from summaries
                join citations
                    on citations.summary_id = summaries.id
                join sources
                    on sources.id = citations.source_id
                where summaries.id in :summary_ids;
            """
            ),
            {"summary_ids": event_ids},
        ).all()
        event_rows = {
            row.event_id: EventRow.model_validate(row, from_attributes=True)
            for row in event_query
        }

        location_query = session.execute(
            text(
                """
                select
                    summaries.id as event_id,
                    tags.id as tag_id,
                    place.latitude,
                    place.longitude
                from summaries
                join taginstances
                    on summaries.id = taginstances.summary_id
                join tags
                    on tags.id = taginstances.tag_id
                join place
                    on place.id = tags.id
                where summaries.id in :summary_ids;
            """
            ),
            {"summary_ids": event_ids},
        )
        location_rows = {
            row.event_id: LocationRow.model_validate(row, from_attributes=True)
            for row in location_query.all()
        }
        calendar_date_query = session.execute(
            text(
                """
                select
                	summaries.id as event_id,
                    time.time as datetime,
                    time.calendar_model as calendar_model,
                    time.precision as precision
                from summaries
                join taginstances
                    on summaries.id = taginstances.summary_id
                join tags
                    on tags.id = taginstances.tag_id
                join time
                    on time.id = tags.id
                where summaries.id in :summary_ids;

            """
            ),
            {"summary_ids": event_ids},
        ).all()
        calendar_date_rows = {
            row.event_id: CalendarDateRow.model_validate(row, from_attributes=True)
            for row in calendar_date_query
        }
        tag_query = session.execute(
            text(
                """
                -- tag rows
                select
                    tags.type as type,
                    summaries.id as event_id,
                    tags.id as tag_id,
                    taginstances.start_char as start_char,
                    taginstances.stop_char as stop_char
                from summaries
                join taginstances
                    on taginstances.summary_id = summaries.id
                join tags
                    on taginstances.tag_id = tags.id
                join tag_name_assoc
                    on tags.id = tag_name_assoc.tag_id
                where summaries.id in :summary_ids;
            """
            ),
            {"summary_ids": event_ids},
        ).all()
        tag_rows: defaultdict[UUID, list[TagRow]] = defaultdict(list)
        for row in tag_query:
            validated_row = TagRow.model_validate(row, from_attributes=True)
            tag_rows[row.event_id].append(validated_row)

        tag_ids = [
            tag_row.tag_id
            for tag_row_list in tag_rows.values()
            for tag_row in tag_row_list
        ]
        tag_name_query = session.execute(
            text(
                """
                select 
                    tags.id as tag_id,
                    array_agg(names.name) as names
                from tags
                join tag_name_assoc
                    on tags.id = tag_name_assoc.tag_id
                join names
                    on names.id = tag_name_assoc.name_id
                where tags.id in :tag_ids
                group by tags.id;
            """
            ),
            {"tag_ids": tuple(tag_ids)},
        ).all()
        tag_names = {
            row.tag_id: TagNames.model_validate(row, from_attributes=True)
            for row in tag_name_query
        }
        unordered_events = {
            event_id: EventQuery(
                event_id=event_id,
                event_row=event_row,
                tags=tag_rows[event_id],
                calendar_date=calendar_date_rows[event_id],
                location_row=location_rows[event_id],
                names=tag_names,
            )
            for event_id, event_row in event_rows.items()
        }
        return [unordered_events[event_id] for event_id in event_ids]

    def get_story_names(
        self, story_ids: tuple[UUID, ...], session: Session
    ) -> dict[UUID, str]:
        rows = session.execute(
            text(
                """
                select
                    tag_id as story_id,
                    name as story_name
                from story_names
                where tag_id in :story_ids;
            """
            ),
            {"story_ids": story_ids},
        ).all()
        return {row.story_id: row.story_name for row in rows}

    def get_coords_by_names(self, names: list[str], session: Session) -> CoordsByName:
        sql = text(
            """
            select names.name, place.latitude, place.longitude 
            from names 
                join tag_name_assoc on names.id = tag_name_assoc.name_id
                join tags on tag_name_assoc.tag_id = tags.id
                join place on tags.id = place.id
            where names.name in :name_list;
        """
        )
        rows = session.execute(sql, {"name_list": tuple(names)}).all()
        coords_by_name = defaultdict(list)
        for name, latitude, longitude in rows:
            coords_by_name[name].append(Coords(latitude=latitude, longitude=longitude))
        return CoordsByName(coords=coords_by_name)

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

    def create_person(
        self,
        id: UUID,
        session: Session,
        wikidata_id: str | None = None,
        wikidata_url: str | None = None,
    ) -> PersonModel:
        stmt = """
                insert into tags (id, type, wikidata_id, wikidata_url)
                values (:id, :type, :wikidata_id, :wikidata_url);
                insert into person (id)
                values (:id);
            """
        session.execute(
            text(stmt),
            {
                "id": id,
                "type": "PERSON",
                "wikidata_id": wikidata_id,
                "wikidata_url": wikidata_url,
            },
        )
        return PersonModel(id=id)

    def get_tag_id_by_wikidata_id(self, wikidata_id: str) -> UUID:
        with Session(self._engine, future=True) as session:
            query = text(
                """
                    select id from tags where wikidata_id = :wikidata_id;
                """
            )
            id = session.execute(
                query, {"wikidata_id": wikidata_id}
            ).scalar_one_or_none()
            return id

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
        wikidata_id: str | None = None,
        wikidata_url: str | None = None,
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
            wikidata_id=wikidata_id,
            wikidata_url=wikidata_url,
        )
        insert_place = """
            insert into tags (id, type, wikidata_id, wikidata_url)
                values (:id, :type, :wikidata_id, :wikidata_url);
            insert into place (id, latitude, longitude, geoshape, geonames_id)
                values (:id, :latitude, :longitude, :geoshape, :geonames_id)
        """
        session.execute(text(insert_place), place_model.model_dump())
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
        wikidata_id: str | None = None,
        wikidata_url: str | None = None,
    ):
        time_model = TimeModel(
            id=id,
            time=time,
            calendar_model=calendar_model,
            precision=precision,
            wikidata_id=wikidata_id,
            wikidata_url=wikidata_url,
        )
        insert_time = """
            insert into tags (id, type, wikidata_id, wikidata_url)
                values (:id, :type, :wikidata_id, :wikidata_url);
            insert into time (id, time, calendar_model, precision)
                values (:id, :time, :calendar_model, :precision);
        """
        session.execute(text(insert_time), time_model.model_dump())
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
        tag_instance_time: datetime,
        time_precision: TimePrecision,
        session: Session,
    ) -> TagInstanceModel:
        story_order = self.get_story_order(
            session=session,
            tag_id=tag_id,
            tag_instance_time=tag_instance_time,
            time_precision=time_precision,
        )
        self.update_story_orders(
            session=session,
            story_order=story_order,
            tag_id=tag_id,
        )
        id = uuid4()
        tag_instance = TagInstanceModel(
            id=id,
            start_char=start_char,
            stop_char=stop_char,
            summary_id=summary_id,
            tag_id=tag_id,
            story_order=story_order,
        )
        stmt = """
            insert into taginstances
                (id, start_char, stop_char, summary_id, tag_id, story_order)
            values
                (:id, :start_char, :stop_char, :summary_id, :tag_id, :story_order)        
        """
        session.execute(text(stmt), tag_instance.model_dump())
        return tag_instance

    def get_story_order(
        self,
        session: Session,
        tag_id: UUID,
        tag_instance_time: datetime,
        time_precision: TimePrecision,
    ) -> int:
        """Given a tag, find the order belonging to a given time."""
        summary_rows = session.execute(
            text(
                """
                select 
                    summaries.id as summary_id,
                    time.time as datetime, 
                    time.precision as precision
                from summaries 
                    -- given a summary, find its time tag
                    join taginstances on taginstances.summary_id = summaries.id
                    join tags on tags.id = taginstances.tag_id and tags.type = 'TIME'
                    join time on time.id = tags.id
                where summaries.id in (
                    -- find all the summaries related to input tag_id
                    select summary_id from taginstances where tag_id = :tag_id
                )
                order by time.time, time.precision
            """
            ),
            {"tag_id": tag_id},
        ).all()
        summary_map = {row.summary_id: row for row in summary_rows}
        if not summary_map:
            return 0

        story_order_rows = session.execute(
            text(
                """
                select 
                    summaries.id as summary_id,
                    taginstances.story_order as story_order
                from summaries
                    join taginstances on taginstances.summary_id = summaries.id
                where summaries.id in :summary_ids
                    and taginstances.tag_id = :tag_id;
            """
            ),
            {
                "summary_ids": tuple([row.summary_id for row in summary_rows]),
                "tag_id": tag_id,
            },
        ).all()
        story_order_map = {row.summary_id: row.story_order for row in story_order_rows}

        story_order = [
            StoryOrder(
                summary_id=summary_id,
                story_order=story_order_map[summary_id],
                datetime=row.datetime,
                precision=row.precision,
            )
            for summary_id, row in summary_map.items()
        ]
        if not story_order:
            return 0
        for row in story_order:
            if row.datetime < tag_instance_time:
                continue
            elif row.datetime == tag_instance_time and row.precision < time_precision:
                continue
            else:
                return row.story_order
        # this tag instance occurs later than all existing tag instances
        return story_order[-1].story_order + 1

    def update_story_orders(
        self, session: Session, tag_id: UUID, story_order: int
    ) -> None:
        """Increment story_order for every row of taginstances with fkey tag_id where the
        current value of story_order is equal or greater than param story_order.
        """
        session.execute(
            text(
                """
                WITH ordered_updates AS (
                    SELECT id 
                    FROM taginstances
                    WHERE tag_id = :tag_id
                      AND story_order >= :story_order
                    ORDER BY story_order DESC
                )
                UPDATE taginstances
                SET story_order = story_order + 1
                FROM ordered_updates
                WHERE taginstances.id = ordered_updates.id;
            """
            ),
            {"tag_id": tag_id, "story_order": story_order},
        )

    def get_time_and_precision_by_tags(
        self, session: Session, tag_ids: list[UUID]
    ) -> tuple[datetime, TimePrecision]:
        """Given a list of tag IDs, find the time and precision associated with them.
        Raises an exception when multiple are found.
        """
        row = session.execute(
            text(
                """
                select 
                    time.time as datetime, time.precision as precision
                from tags
                join time on tags.id = time.id
                where tags.id in :tag_ids;
            """
            ),
            {"tag_ids": tuple(tag_ids)},
        ).one()
        return row.datetime, row.precision

    def exists_tag(self, tag_id: UUID, session: Session) -> bool:
        get_tag = "select id from tags where tags.id = :tag_id"
        tag_id = session.execute(text(get_tag), {"tag_id": tag_id}).scalar_one_or_none()
        return tag_id is not None

    def get_tags_by_wikidata_ids(self, wikidata_ids: list[str]) -> list[TagPointer]:
        if not wikidata_ids:
            return []
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select id, wikidata_id
                    from tags 
                    where wikidata_id in :wikidata_ids;
                """
                ),
                {"wikidata_ids": tuple(wikidata_ids)},
            ).all()
        tag_pointers = [
            TagPointer(
                id=row.id,
                wikidata_id=row.wikidata_id,
            )
            for row in rows
        ]
        existing_wiki_ids = {tag.wikidata_id for tag in tag_pointers}
        for wikidata_id in wikidata_ids:
            if wikidata_id not in existing_wiki_ids:
                tag_pointers.append(TagPointer(wikidata_id=wikidata_id))
        return tag_pointers

    def add_name_to_tag(
        self, session: Session, tag_id: UUID, name: str, lang: str | None = None
    ):
        """Ensure name exists, and associate it with the tag."""
        # todo: handle lang
        name_model = self.get_name(name=name, session=session)
        if name_model is None:
            name_model = self.create_name(name=name, session=session)
        else:
            # check that this name/tag combo doesn't exist
            existing_row = session.execute(
                text(
                    """
                    select * from tag_name_assoc where tag_id = :tag_id and name_id = :name_id
                """,
                    {"tag_id": tag_id, "name_id": name_model.id},
                )
            ).one_or_none()
            if existing_row:
                return

        tag_name_assoc = TagNameAssocModel(name_id=name_model.id, tag_id=tag_id)

        stmt = """
            insert into tag_name_assoc (tag_id, name_id)
                values (:tag_id, :name_id);
        """
        session.execute(text(stmt), tag_name_assoc.model_dump())

    def add_story_names(
        self, tag_id: UUID, session: Session, story_names: list[StoryName]
    ) -> None:
        session.execute(
            text(
                """
                insert into story_names (id, tag_id, name, lang)
                values (:id, :tag_id, :name, :lang)
            """
            ),
            [
                {
                    "id": uuid4(),
                    "tag_id": tag_id,
                    "name": story_name.name,
                    "lang": story_name.lang,
                }
                for story_name in story_names
            ],
        )

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

    def get_source_by_title(self, title: str) -> ADMSource | None:
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    select id, title, author, publisher, pub_date from sources where title = :title;
                """
                ),
                {"title": title},
            ).one_or_none()
            if not row:
                return None
            return ADMSource(
                id=str(row.id),
                title=row.title,
                author=row.author,
                publisher=row.publisher,
                pub_date=str(row.pub_date),
            )

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
