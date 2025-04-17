import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import (
    Tuple,
    Optional,
    List,
    Literal,
    Any,
    Callable,
    ClassVar,
    TypeVar,
    cast,
)
from uuid import uuid4, UUID
from enum import Enum

from sqlalchemy import select, text, create_engine, orm, insert
from sqlalchemy.orm import Session, sessionmaker

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.core import (
    TagPointer,
    StoryOrder,
    StoryName,
    StoryPointer,
)
from the_history_atlas.apps.domain.models.history import (
    Source as ADMSource,
)
from the_history_atlas.apps.domain.models.history.get_fuzzy_search_by_name import (
    FuzzySearchByName,
)
from the_history_atlas.apps.domain.models.history.get_events import (
    EventQuery,
    EventRow,
    TagRow,
    CalendarDateRow,
    LocationRow,
    TagNames,
)
from the_history_atlas.apps.domain.models.history.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TagNameAssocModel,
    SummaryModel,
)
from the_history_atlas.apps.domain.models.history.tables.time import (
    TimePrecision,
    TimeModel,
)
from the_history_atlas.apps.history.errors import MissingResourceError
from the_history_atlas.apps.history.schema import (
    Base,
    Person,
    Place,
    Summary,
    Time,
    Source,
    Tag,
    TagInstance,
)
from the_history_atlas.apps.history.trie import Trie
from the_history_atlas.apps.history.tracing import trace_db, trace_method, trace_block

log = logging.getLogger(__name__)


class Repository:

    Session: sessionmaker

    def __init__(self, database_client: DatabaseClient, source_trie: Trie):
        self._source_trie = source_trie
        self._engine = database_client

        self.Session = sessionmaker(bind=database_client)
        Base.metadata.create_all(self._engine)

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
        """Search for possible completions to a given string from known entity names using PostgreSQL."""
        if name == "":
            return []

        # Use PostgreSQL trigram similarity search
        with Session(self._engine, future=True) as session:
            # Query for names that match using trigram similarity
            query = text(
                """
                SELECT 
                    names.name, 
                    ARRAY_AGG(tag_names.tag_id) AS ids
                FROM names
                JOIN tag_names ON names.id = tag_names.name_id
                WHERE similarity(names.name, :search_term) > 0.3
                   OR names.name ILIKE :like_pattern
                GROUP BY names.name
                ORDER BY similarity(names.name, :search_term) DESC
                LIMIT 10
            """
            )

            results = session.execute(
                query, {"search_term": name, "like_pattern": f"%{name}%"}
            ).all()

            return [
                FuzzySearchByName(
                    name=row.name, ids=row.ids  # The ids are already UUID objects
                )
                for row in results
            ]

    def get_default_story_and_event(
        self,
    ) -> StoryPointer:
        with Session(self._engine, future=True) as session:
            # get the beginning of a person's life
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    JOIN tags ON tag_instances.tag_id = tags.id
                    WHERE tag_instances.story_order = 0
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
        # given a story, return the first event
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    WHERE tag_instances.story_order = 0
                    AND tag_instances.tag_id = :story_id
                """
                ),
                {"story_id": story_id},
            ).one()
            return StoryPointer(
                event_id=row.event_id,
                story_id=row.story_id,
            )

    def get_default_story_by_event(self, event_id: UUID) -> StoryPointer:
        with Session(self._engine, future=True) as session:
            # given an event, always return a person's story
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    JOIN tags ON tag_instances.tag_id = tags.id
                    WHERE tag_instances.story_order = 0
                    AND tags.type = 'PERSON'
                    AND tag_instances.tag_id = :event_id
                    ORDER BY RANDOM()
                    LIMIT 1;
                """
                ),
                {"event_id": event_id},
            ).one()
            return StoryPointer(
                event_id=row.event_id,
                story_id=row.story_id,
            )

    def get_story_pointers(
        self,
        summary_id: UUID,
        tag_id: UUID,
        direction: Literal["next", "prev"] | None,
        session: Session,
    ) -> List[StoryPointer]:
        # todo: remove direction=None
        match direction:
            case "next":
                operator = ">"
                predicate = ""
                order_by_clause = "asc"
            case "prev":
                operator = "<"
                predicate = ""
                order_by_clause = "desc"
            case None:
                operator = ">="
                predicate = "- 5"
                order_by_clause = "asc"
            case _:
                raise RuntimeError("Unknown direction")
        query = f"""
                select 
                    ti.summary_id as event_id,
                    ti.tag_id as story_id
                from tag_instances ti
                where ti.tag_id = :tag_id
                and ti.story_order {operator} (
                    select story_order from tag_instances
                    where tag_instances.tag_id =  :tag_id
                    and tag_instances.summary_id = :summary_id
                ) {predicate}
                order by ti.story_order {order_by_clause}
                limit 10
            """
        rows = session.execute(
            text(query), {"tag_id": tag_id, "summary_id": summary_id}
        ).all()
        story_pointers = [
            StoryPointer.model_validate(row, from_attributes=True) for row in rows
        ]
        if direction == "prev":
            story_pointers.reverse()
        return story_pointers

    def get_related_story(
        self,
        summary_id: UUID,
        tag_id: UUID,
        direction: Literal["next", "prev"],
        session: Session,
    ) -> StoryPointer | None:
        related_tags = session.execute(
            text(
                """
                select
                    tags.id as tag_id,
                    tags.type as tag_type
                from summaries
                join tag_instances on summaries.id = tag_instances.summary_id
                join tags ON tag_instances.tag_id = tags.id
                where summaries.id = :summary_id;
            """
            ),
            {"summary_id": summary_id},
        ).all()
        related_tags_by_id = {row.tag_id: row.tag_type for row in related_tags}
        # this logic currently assumes one tag per type
        related_tags_by_type = {val: key for key, val in related_tags_by_id.items()}
        tag_type = related_tags_by_id.get(tag_id)
        if tag_type == "PERSON":
            story_id = related_tags_by_type.get("PLACE")
        elif tag_type == "PLACE":
            story_id = related_tags_by_type.get("TIME")
        else:
            time_story_id = related_tags_by_type.get("TIME")
            if not time_story_id:
                return None
            story_id = self.get_related_time_story(
                story_id=time_story_id,
                direction=direction,
                session=session,
            )
        if not story_id:
            return None
        last_datetime, last_precision = self.get_time_and_precision_by_tags(
            session=session, tag_ids=list(related_tags_by_id.keys())
        )
        event_id = self.get_closest_summary_id(
            story_id=story_id,
            datetime=last_datetime,
            precision=last_precision,
            direction=direction,
            session=session,
        )
        if not event_id:
            return None
        return StoryPointer(
            event_id=event_id,
            story_id=story_id,
        )

    def get_related_time_story(
        self, story_id: UUID, direction: Literal["next", "prev"], session: Session
    ) -> UUID | None:
        match direction:
            case "next":
                operator = ">"
                order_by_clause = "asc"
            case "prev":
                operator = "<"
                order_by_clause = "desc"
            case _:
                raise RuntimeError("Unknown direction")
        # todo: doesnt account for precision
        next_story_id = session.execute(
            text(
                f"""
                 select 
                 times.id
                 from times
                 where times.datetime {operator} (
                    select times.datetime
                    from tags
                    join times
                    on tags.id = times.id
                    where tags.id = :tag_id
                )
                order by times.datetime {order_by_clause}
                limit 1;
            """
            ),
            {"tag_id": story_id},
        ).scalar_one_or_none()
        return next_story_id

    def get_closest_summary_id(
        self,
        story_id: UUID,
        datetime: datetime,
        precision: TimePrecision,
        direction: Literal["next", "prev"],
        session: Session,
    ) -> UUID | None:
        # todo: account for precision
        match direction:
            case "next":
                operator = ">"
                order_by_clause = "asc"
            case "prev":
                operator = "<"
                order_by_clause = "desc"
            case _:
                raise RuntimeError("Unknown direction")
        return session.execute(
            text(
                f"""
                select
                    summaries.id as summary_id
                from summaries
                join tag_instances on summaries.id = tag_instances.summary_id
                join tags on tag_instances.tag_id = tags.id
                join times on times.id = tags.id
                where summaries.id in (
                    select summaries.id from summaries
                    join tag_instances on summaries.id = tag_instances.summary_id
                    where tag_instances.tag_id = :tag_id
                )
                and times.datetime {operator} :datetime
                order by times.datetime {order_by_clause}
                limit 1;
            """
            ),
            {"tag_id": story_id, "datetime": datetime},
        ).scalar_one_or_none()

    def get_events(
        self, event_ids: tuple[UUID, ...], session: Session
    ) -> list[EventQuery]:
        if not event_ids:
            return []
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
        if not event_rows:
            raise MissingResourceError("No events found")

        location_query = session.execute(
            text(
                """
                select
                    summaries.id as event_id,
                    tags.id as tag_id,
                    places.latitude,
                    places.longitude
                from summaries
                join tag_instances
                    on summaries.id = tag_instances.summary_id
                join tags
                    on tags.id = tag_instances.tag_id
                join places
                    on places.id = tags.id
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
                    times.datetime as datetime,
                    times.calendar_model as calendar_model,
                    times.precision as precision
                from summaries
                join tag_instances
                    on summaries.id = tag_instances.summary_id
                join tags
                    on tags.id = tag_instances.tag_id
                join times
                    on times.id = tags.id
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
                    tag_instances.start_char as start_char,
                    tag_instances.stop_char as stop_char
                from summaries
                join tag_instances
                    on tag_instances.summary_id = summaries.id
                join tags
                    on tag_instances.tag_id = tags.id
                join tag_names
                    on tags.id = tag_names.tag_id
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
                join tag_names
                    on tags.id = tag_names.tag_id
                join names
                    on names.id = tag_names.name_id
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
    ) -> dict[UUID, dict[str, str]]:
        rows = session.execute(
            text(
                """
                select
                    tag_id as story_id,
                    name as story_name,
                    description
                from story_names
                where tag_id in :story_ids;
            """
            ),
            {"story_ids": story_ids},
        ).all()
        return {
            row.story_id: {"name": row.story_name, "description": row.description}
            for row in rows
        }

    @trace_db("create_summary")
    def create_summary(self, id: UUID, text: str) -> None:
        """Creates a new summary"""
        log.info(f"Creating a new summary: {text[:50]}...")
        summary = Summary(id=id, text=text)
        with Session(self._engine, future=True) as session:
            session.add(summary)
            session.commit()

    @trace_db("create_citation")
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

    @trace_db("create_citation_source_fkey")
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

    @trace_db("create_citation_summary_fkey")
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

    @trace_db("create_citation_complete")
    def create_citation_complete(
        self,
        session: Session,
        id: UUID,
        citation_text: str,
        source_id: UUID,
        summary_id: UUID,
        access_date: Optional[str] = None,
        page_num: Optional[int] = None,
    ) -> None:
        """Creates a citation with all relationships in a single database operation"""
        stmt = """
            INSERT INTO citations 
                (id, text, source_id, summary_id, page_num, access_date)
            VALUES 
                (:id, :text, :source_id, :summary_id, :page_num, :access_date)
        """
        session.execute(
            text(stmt),
            {
                "id": id,
                "text": citation_text,
                "source_id": source_id,
                "summary_id": summary_id,
                "page_num": page_num,
                "access_date": access_date,
            },
        )

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
                insert into people (id)
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
            select id, latitude, longitude, geoshape 
            from places where places.id = :id;
        """
        res = session.execute(text(stmt), {"id": id}).one_or_none()
        if res is None:
            return None
        return PlaceModel(
            id=res[0],
            latitude=res[1],
            longitude=res[2],
            geoshape=res[3],
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
    ) -> PlaceModel:
        place_model = PlaceModel(
            id=id,
            latitude=latitude,
            longitude=longitude,
            geoshape=geoshape,
            wikidata_id=wikidata_id,
            wikidata_url=wikidata_url,
        )
        insert_place = """
            insert into tags (id, type, wikidata_id, wikidata_url)
                values (:id, :type, :wikidata_id, :wikidata_url);
            insert into places (id, latitude, longitude, geoshape)
                values (:id, :latitude, :longitude, :geoshape)
        """
        session.execute(text(insert_place), place_model.model_dump())
        return place_model

    def create_time(
        self,
        session: Session,
        id: UUID,
        datetime: datetime,
        calendar_model: str,
        precision: TimePrecision,
        wikidata_id: str | None = None,
        wikidata_url: str | None = None,
    ):
        time_model = TimeModel(
            id=id,
            datetime=datetime,
            calendar_model=calendar_model,
            precision=precision,
            wikidata_id=wikidata_id,
            wikidata_url=wikidata_url,
        )
        insert_time = """
            insert into tags (id, type, wikidata_id, wikidata_url)
                values (:id, :type, :wikidata_id, :wikidata_url);
            insert into times (id, datetime, calendar_model, precision)
                values (:id, :datetime, :calendar_model, :precision);
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

    @trace_db("create_tag_instance")
    def create_tag_instance(
        self,
        start_char: int,
        stop_char: int,
        summary_id: UUID,
        tag_id: UUID,
        tag_instance_time: str,
        time_precision: TimePrecision,
        after: list[UUID],
        session: Session,
    ) -> TagInstanceModel:
        with trace_block("get_story_order"):
            story_order = self.get_story_order(
                session=session,
                tag_id=tag_id,
                tag_instance_time=tag_instance_time,
                time_precision=time_precision,
                after=after,
            )

        with trace_block("update_story_orders"):
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

        with trace_block("execute_tag_instance_insert"):
            stmt = """
                insert into tag_instances
                    (id, start_char, stop_char, summary_id, tag_id, story_order)
                values
                    (:id, :start_char, :stop_char, :summary_id, :tag_id, :story_order)        
            """
            session.execute(text(stmt), tag_instance.model_dump())

        return tag_instance

    @trace_db("get_story_order")
    def get_story_order(
        self,
        session: Session,
        tag_id: UUID,
        tag_instance_time: str,
        time_precision: TimePrecision,
        after: list[UUID],
    ) -> int:
        """Given a tag, find the order belonging to a given time."""
        summary_rows = session.execute(
            text(
                """
                select 
                    summaries.id as summary_id,
                    times.datetime as datetime, 
                    times.precision as precision
                from summaries 
                    -- given a summary, find its time tag
                    join tag_instances on tag_instances.summary_id = summaries.id
                    join tags on tags.id = tag_instances.tag_id and tags.type = 'TIME'
                    join times on times.id = tags.id
                where summaries.id in (
                    -- find all the summaries related to input tag_id
                    select summary_id from tag_instances where tag_id = :tag_id
                )
                order by times.datetime, times.precision
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
                    tag_instances.story_order as story_order
                from summaries
                    join tag_instances on tag_instances.summary_id = summaries.id
                where summaries.id in :summary_ids
                    and tag_instances.tag_id = :tag_id;
            """
            ),
            {
                "summary_ids": tuple([row.summary_id for row in summary_rows]),
                "tag_id": tag_id,
            },
        ).all()
        story_order_map = {row.summary_id: row.story_order for row in story_order_rows}

        story_order = sorted(
            [
                StoryOrder(
                    summary_id=summary_id,
                    story_order=story_order_map[summary_id],
                    datetime=row.datetime,
                    precision=row.precision,
                )
                for summary_id, row in summary_map.items()
            ],
            key=lambda row: row.story_order,
        )
        if not story_order:
            return 0
        for row in story_order:
            if row.datetime < tag_instance_time:
                continue
            elif row.datetime == tag_instance_time and row.precision < time_precision:
                continue
            elif row.summary_id in after:
                # make a best effort to put this summary after the given IDs,
                # but only if the time matches
                continue
            else:
                return row.story_order
        # this tag instance occurs later than all existing tag instances
        return story_order[-1].story_order + 1

    @trace_db("update_story_orders")
    def update_story_orders(
        self, session: Session, tag_id: UUID, story_order: int
    ) -> None:
        """Increment story_order for every row of tag_instances with fkey tag_id where the
        current value of story_order is equal or greater than param story_order.
        """
        OFFSET = 10_000_000
        session.execute(
            text(
                """
                UPDATE tag_instances
                SET story_order = story_order + :offset 
                WHERE tag_id = :tag_id
                  AND story_order >= :story_order;

                UPDATE tag_instances
                SET story_order = story_order - (:offset - 1) 
                WHERE tag_id = :tag_id
                  AND story_order >= :story_order + :offset;
            """
            ),
            {"tag_id": tag_id, "story_order": story_order, "offset": OFFSET},
        )

    def get_time_and_precision_by_tags(
        self, session: Session, tag_ids: list[UUID]
    ) -> tuple[str, TimePrecision]:
        """Given a list of tag IDs, find the time and precision associated with them.
        Raises an exception when multiple are found.
        """
        row = session.execute(
            text(
                """
                select 
                    times.datetime as datetime, times.precision as precision
                from tags
                join times on tags.id = times.id
                where tags.id in :tag_ids;
            """
            ),
            {"tag_ids": tuple(tag_ids)},
        ).one()
        return row.datetime, row.precision

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
            assert tag_id
            existing_row = session.execute(
                text(
                    """
                    select * from tag_names where tag_names.tag_id = :tag_id and tag_names.name_id = :name_id;
                """
                ),
                {"tag_id": tag_id, "name_id": name_model.id},
            ).one_or_none()
            if existing_row:
                return

        tag_names = TagNameAssocModel(name_id=name_model.id, tag_id=tag_id)

        stmt = """
            insert into tag_names (tag_id, name_id)
                values (:tag_id, :name_id);
        """
        session.execute(text(stmt), tag_names.model_dump())

    def add_story_names(
        self, tag_id: UUID, session: Session, story_names: list[StoryName]
    ) -> None:
        session.execute(
            text(
                """
                insert into story_names (id, tag_id, name, lang, description)
                values (:id, :tag_id, :name, :lang, :description)
            """
            ),
            [
                {
                    "id": uuid4(),
                    "tag_id": tag_id,
                    "name": story_name.name,
                    "lang": story_name.lang,
                    "description": story_name.description,
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
        pub_date: str | None,
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

    def update_entity_trie(
        self,
        new_string=None,
        new_string_guid=None,
        old_string=None,
        old_string_guid=None,
    ):
        """
        This method is now a no-op as we use PostgreSQL for text search instead of an in-memory trie.
        The method signature is kept for backwards compatibility.
        """
        pass

    def time_exists(
        self,
        datetime: str,
        calendar_model: str,
        precision: TimePrecision,
        session: Session,
    ) -> UUID | None:
        """Check if a time with the given parameters exists in the database.

        Args:
            datetime: The datetime string to check
            calendar_model: The calendar model to check
            precision: The time precision to check
            session: The database session

        Returns:
            tuple: (exists, id) where exists is True if a matching time exists, False otherwise
                  and id is the UUID of the matching time if exists is True, None otherwise
        """
        row = session.execute(
            text(
                """
                select id from times
                where datetime = :datetime
                and calendar_model = :calendar_model
                and precision = :precision
            """
            ),
            {
                "datetime": datetime,
                "calendar_model": calendar_model,
                "precision": precision,
            },
        ).scalar_one_or_none()

        return row

    @trace_db("bulk_create_tag_instances")
    def bulk_create_tag_instances(
        self,
        tag_instances: list[dict],
        tag_instance_time: str,
        time_precision: TimePrecision,
        after: list[UUID],
        session: Session,
    ) -> list[TagInstanceModel]:
        """Create multiple tag instances in a single operation for better performance."""
        # Group tag instances by tag_id for efficient story ordering
        instances_by_tag = defaultdict(list)
        for instance in tag_instances:
            instances_by_tag[instance["tag_id"]].append(instance)

        # Process each tag group
        result_instances = []

        for tag_id, instances in instances_by_tag.items():
            # Get the starting story order for this tag
            with trace_block(f"get_story_order_for_tag_{tag_id}"):
                story_order = self.get_story_order(
                    session=session,
                    tag_id=tag_id,
                    tag_instance_time=tag_instance_time,
                    time_precision=time_precision,
                    after=after,
                )

            # Update existing story orders in one operation
            with trace_block(f"update_story_orders_for_tag_{tag_id}"):
                self.update_story_orders(
                    session=session,
                    story_order=story_order,
                    tag_id=tag_id,
                )

            # Prepare all instances for this tag
            models = []
            values = []

            for i, instance in enumerate(instances):
                instance_id = uuid4()
                current_order = story_order + i

                model = TagInstanceModel(
                    id=instance_id,
                    start_char=instance["start_char"],
                    stop_char=instance["stop_char"],
                    summary_id=instance["summary_id"],
                    tag_id=tag_id,
                    story_order=current_order,
                )
                models.append(model)

                values.append(
                    {
                        "id": instance_id,
                        "start_char": instance["start_char"],
                        "stop_char": instance["stop_char"],
                        "summary_id": instance["summary_id"],
                        "tag_id": tag_id,
                        "story_order": current_order,
                    }
                )

            # Bulk insert all instances for this tag
            with trace_block(f"bulk_insert_for_tag_{tag_id}"):
                if values:
                    placeholders = []
                    all_params = {}

                    for i, val in enumerate(values):
                        placeholder = f"(:id_{i}, :start_char_{i}, :stop_char_{i}, :summary_id_{i}, :tag_id_{i}, :story_order_{i})"
                        placeholders.append(placeholder)

                        for key, value in val.items():
                            all_params[f"{key}_{i}"] = value

                    stmt = f"""
                        INSERT INTO tag_instances
                            (id, start_char, stop_char, summary_id, tag_id, story_order)
                        VALUES
                            {', '.join(placeholders)}
                    """
                    session.execute(text(stmt), all_params)

            result_instances.extend(models)

        return result_instances

    def update_order_story_bulk(self, story_id: UUID) -> None: ...
