import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import (
    Tuple,
    Optional,
    List,
    Literal,
    Dict,
)
from uuid import uuid4, UUID

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.core import (
    TagPointer,
    StoryOrder,
    StoryName,
    StoryPointer,
    TagInstanceWithTime,
    TagInstanceWithTimeAndOrder,
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
from the_history_atlas.apps.domain.models.history.get_nearby_events import (
    NearbyEventRow,
)
from the_history_atlas.apps.domain.models.history.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TagNameAssocModel,
)
from the_history_atlas.apps.domain.models.history.tables.tag_instance import (
    TagInstanceInput,
)
from the_history_atlas.apps.domain.models.history.tables.time import (
    TimePrecision,
    TimeModel,
)
from the_history_atlas.apps.history.errors import MissingResourceError
from the_history_atlas.apps.history.schema import (
    Base,
    Summary,
    Source,
)
from the_history_atlas.apps.domain.models.history.tables.theme import (
    ThemeModel,
    ThemeWithChildrenModel,
    SummaryThemeModel,
)
from the_history_atlas.apps.history.trie import Trie

log = logging.getLogger(__name__)


class RebalanceError(Exception):
    """Story orders require rebalancing"""

    pass


class Repository:

    Session: sessionmaker

    def __init__(self, database_client: DatabaseClient, source_trie: Trie):
        self._source_trie = source_trie
        self._engine = database_client

        self.Session = sessionmaker(bind=database_client)
        Base.metadata.create_all(self._engine)

        # Cache for default story and event
        self._default_story_cache = []
        self._cache_lock = threading.RLock()
        self._cache_refresh_thread = None
        self._stop_cache_refresh = threading.Event()

    def start_cache_refresh_thread(self, refresh_interval_seconds=3600):
        """Start a background thread to periodically refresh the cache"""
        if (
            self._cache_refresh_thread is not None
            and self._cache_refresh_thread.is_alive()
        ):
            log.warning("Cache refresh thread is already running")
            return

        self._stop_cache_refresh.clear()
        self._cache_refresh_thread = threading.Thread(
            target=self._cache_refresh_worker,
            args=(refresh_interval_seconds,),
            daemon=True,
            name="DefaultStoryCacheRefresher",
        )
        self._cache_refresh_thread.start()
        log.info(
            f"Started cache refresh thread with interval {refresh_interval_seconds} seconds"
        )

    def stop_cache_refresh_thread(self):
        """Stop the background cache refresh thread"""
        if (
            self._cache_refresh_thread is not None
            and self._cache_refresh_thread.is_alive()
        ):
            log.info("Stopping cache refresh thread")
            self._stop_cache_refresh.set()
            self._cache_refresh_thread.join(timeout=5.0)
            if self._cache_refresh_thread.is_alive():
                log.warning("Cache refresh thread did not stop within timeout")
            else:
                log.info("Cache refresh thread stopped successfully")
        self._cache_refresh_thread = None

    def _cache_refresh_worker(self, refresh_interval_seconds):
        """Worker function for the cache refresh thread"""
        log.info("Cache refresh thread started")
        while not self._stop_cache_refresh.is_set():
            try:
                self.prime_default_story_cache()
                # Sleep for the refresh interval, but check for stop signal every second
                for _ in range(refresh_interval_seconds):
                    if self._stop_cache_refresh.is_set():
                        break
                    time.sleep(1)
            except Exception as e:
                log.error(f"Error refreshing default story cache: {e}")
                # Sleep for a shorter period after error
                time.sleep(60)

    def prime_default_story_cache(self, cache_size=100):
        """Prime the cache with default story and event combinations"""
        log.info(f"Priming default story cache with {cache_size} entries")
        with Session(self._engine, future=True) as session:
            try:
                # Get random person stories with valid story_order
                rows = session.execute(
                    text(
                        """
                        SELECT summary_id as event_id, tag_id as story_id
                        FROM tag_instances
                        JOIN tags ON tag_instances.tag_id = tags.id
                        WHERE tag_instances.story_order IS NOT NULL
                        AND tags.type = 'PERSON'
                        ORDER BY RANDOM()
                        LIMIT :limit;
                        """
                    ),
                    {"limit": cache_size},
                ).all()

                with self._cache_lock:
                    self._default_story_cache = [
                        {"event_id": row.event_id, "story_id": row.story_id}
                        for row in rows
                    ]
                log.info(
                    f"Default story cache primed with {len(self._default_story_cache)} entries"
                )
            except Exception as e:
                log.error(f"Failed to prime default story cache: {e}")
                # Keep the existing cache if there was an error

    def get_default_story_and_event(
        self,
    ) -> StoryPointer:
        """Get a default story and event, using the cache if available"""
        with self._cache_lock:
            if not self._default_story_cache:
                # Cache is empty, build it now
                log.info("Default story cache is empty, building it now")
                self.prime_default_story_cache()

            if self._default_story_cache:
                # Use a random entry from the cache
                import random

                cache_entry = random.choice(self._default_story_cache)
                return StoryPointer(
                    event_id=cache_entry["event_id"],
                    story_id=cache_entry["story_id"],
                )

        # Fallback to direct database query if cache is still empty
        log.warning("Using fallback direct database query for default story and event")
        with Session(self._engine, future=True) as session:
            # get the beginning of a person's life
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    JOIN tags ON tag_instances.tag_id = tags.id
                    AND tag_instances.story_order IS NOT NULL
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

    def get_tag_ids_with_null_orders(
        self,
        session: Session,
        start_tag_id: Optional[UUID] = None,
        stop_tag_id: Optional[UUID] = None,
    ) -> List[UUID]:
        """
        Returns a list of tag IDs that have at least one related tag_instance with a null story_order.
        The list is ordered by tag ID.

        Args:
            start_tag_id: Optional UUID to start the result set from (inclusive)
            stop_tag_id: Optional UUID to end the result set at (inclusive)
            session: SQLAlchemy session to use

        Returns:
            List[UUID]: A list of tag IDs ordered by ID
        """
        base_query = """
            SELECT DISTINCT tags.id
            FROM tags
            JOIN tag_instances ON tags.id = tag_instances.tag_id
            WHERE tag_instances.story_order IS NULL
        """

        conditions = []
        params = {}

        if start_tag_id is not None:
            conditions.append("tags.id >= :start_tag_id")
            params["start_tag_id"] = start_tag_id

        if stop_tag_id is not None:
            conditions.append("tags.id <= :stop_tag_id")
            params["stop_tag_id"] = stop_tag_id

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY tags.id"

        query = text(base_query)
        rows = session.execute(query, params).all()
        return [row[0] for row in rows]

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

    def get_default_event_by_story(self, story_id: UUID) -> StoryPointer:
        # given a story, return the first event
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    where tag_instances.story_order IS NOT NULL
                    AND tag_instances.tag_id = :story_id
                    ORDER BY tag_instances.story_order
                    LIMIT 1;
                """
                ),
                {"story_id": story_id},
            ).one_or_none()
            if row:
                return StoryPointer(event_id=row.event_id, story_id=row.story_id)

            # Fall back to text-reader story (story_summaries table)
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, story_id
                    FROM story_summaries
                    WHERE story_id = :story_id
                    ORDER BY position
                    LIMIT 1;
                """
                ),
                {"story_id": story_id},
            ).one()
            return StoryPointer(event_id=row.event_id, story_id=row.story_id)

    def get_default_story_by_event(self, event_id: UUID) -> StoryPointer:
        with Session(self._engine, future=True) as session:
            # given an event, always return a person's story
            row = session.execute(
                text(
                    """
                    SELECT summary_id as event_id, tag_id as story_id
                    FROM tag_instances
                    JOIN tags ON tag_instances.tag_id = tags.id
                    AND tag_instances.story_order IS NOT NULL
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
                and ti.story_order IS NOT NULL
                and ti.story_order {operator} (
                    select story_order from tag_instances
                    where tag_instances.tag_id =  :tag_id
                    and tag_instances.summary_id = :summary_id
                    and tag_instances.story_order IS NOT NULL
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
    ) -> dict[UUID, dict]:
        rows = session.execute(
            text(
                """
                SELECT
                    sn.tag_id AS story_id,
                    sn.name AS story_name,
                    sn.description,
                    MIN(
                        CASE
                            WHEN s.datetime LIKE '+%' THEN CAST(SUBSTRING(s.datetime, 2, 4) AS INTEGER)
                            WHEN s.datetime LIKE '-%' THEN -CAST(SUBSTRING(s.datetime, 2, 4) AS INTEGER)
                            ELSE NULL
                        END
                    ) AS earliest_year,
                    MAX(
                        CASE
                            WHEN s.datetime LIKE '+%' THEN CAST(SUBSTRING(s.datetime, 2, 4) AS INTEGER)
                            WHEN s.datetime LIKE '-%' THEN -CAST(SUBSTRING(s.datetime, 2, 4) AS INTEGER)
                            ELSE NULL
                        END
                    ) AS latest_year
                FROM story_names sn
                LEFT JOIN tag_instances ti ON ti.tag_id = sn.tag_id
                LEFT JOIN summaries s ON s.id = ti.summary_id AND s.datetime IS NOT NULL
                WHERE sn.tag_id IN :story_ids
                GROUP BY sn.tag_id, sn.name, sn.description;
            """
            ),
            {"story_ids": story_ids},
        ).all()
        result = {
            row.story_id: {
                "name": row.story_name,
                "description": row.description,
                "earliest_year": row.earliest_year,
                "latest_year": row.latest_year,
            }
            for row in rows
        }

        # Also look up text-reader stories for any IDs not found in story_names
        missing_ids = tuple(sid for sid in story_ids if sid not in result)
        if missing_ids:
            tr_rows = session.execute(
                text(
                    """
                    SELECT
                        s.id AS story_id,
                        s.name AS story_name,
                        s.description,
                        MIN(
                            CASE
                                WHEN su.datetime LIKE '+%' THEN CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                WHEN su.datetime LIKE '-%' THEN -CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                ELSE NULL
                            END
                        ) AS earliest_year,
                        MAX(
                            CASE
                                WHEN su.datetime LIKE '+%' THEN CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                WHEN su.datetime LIKE '-%' THEN -CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                ELSE NULL
                            END
                        ) AS latest_year
                    FROM stories s
                    LEFT JOIN story_summaries ss ON ss.story_id = s.id
                    LEFT JOIN summaries su ON su.id = ss.summary_id AND su.datetime IS NOT NULL
                    WHERE s.id IN :missing_ids
                    GROUP BY s.id, s.name, s.description;
                """
                ),
                {"missing_ids": missing_ids},
            ).all()
            for row in tr_rows:
                result[row.story_id] = {
                    "name": row.story_name,
                    "description": row.description,
                    "earliest_year": row.earliest_year,
                    "latest_year": row.latest_year,
                }

        return result

    def is_text_reader_story(self, story_id: UUID, session: Session) -> bool:
        """Return True if story_id belongs to a text-reader story (stories table)."""
        row = session.execute(
            text("SELECT 1 FROM stories WHERE id = :story_id"),
            {"story_id": story_id},
        ).one_or_none()
        return row is not None

    def get_text_reader_story_pointers(
        self,
        story_id: UUID,
        summary_id: UUID,
        direction: Literal["next", "prev"] | None,
        session: Session,
    ) -> list[StoryPointer]:
        """Return story pointers from story_summaries for a text-reader story."""
        match direction:
            case "next":
                operator = ">"
                order_by = "asc"
                offset_clause = ""
            case "prev":
                operator = "<"
                order_by = "desc"
                offset_clause = ""
            case _:
                operator = ">"
                order_by = "asc"
                offset_clause = "- 5"

        query = f"""
            SELECT ss.summary_id AS event_id, ss.story_id
            FROM story_summaries ss
            WHERE ss.story_id = :story_id
            AND ss.position {operator} (
                SELECT position FROM story_summaries
                WHERE story_id = :story_id AND summary_id = :summary_id
            ) {offset_clause}
            ORDER BY ss.position {order_by}
            LIMIT 10
        """
        rows = session.execute(
            text(query), {"story_id": story_id, "summary_id": summary_id}
        ).all()
        pointers = [
            StoryPointer(event_id=row.event_id, story_id=row.story_id) for row in rows
        ]
        if direction == "prev":
            pointers.reverse()
        return pointers

    def search_stories_by_name(self, name: str) -> list[dict]:
        """Search text-reader stories by name using fuzzy matching."""
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    SELECT
                        s.id,
                        s.name,
                        s.description,
                        MIN(
                            CASE
                                WHEN su.datetime LIKE '+%' THEN CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                WHEN su.datetime LIKE '-%' THEN -CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                ELSE NULL
                            END
                        ) AS earliest_year,
                        MAX(
                            CASE
                                WHEN su.datetime LIKE '+%' THEN CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                WHEN su.datetime LIKE '-%' THEN -CAST(SUBSTRING(su.datetime, 2, 4) AS INTEGER)
                                ELSE NULL
                            END
                        ) AS latest_year
                    FROM stories s
                    LEFT JOIN story_summaries ss ON ss.story_id = s.id
                    LEFT JOIN summaries su ON su.id = ss.summary_id AND su.datetime IS NOT NULL
                    WHERE s.name ILIKE :like_pattern
                       OR similarity(s.name, :search_term) > 0.3
                    GROUP BY s.id, s.name, s.description
                    ORDER BY similarity(s.name, :search_term) DESC
                    LIMIT 10
                """
                ),
                {"search_term": name, "like_pattern": f"%{name}%"},
            ).all()
            return [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "earliestYear": row.earliest_year,
                    "latestYear": row.latest_year,
                }
                for row in rows
            ]

    def create_summary(
        self,
        id: UUID,
        text: str,
        datetime: str | None = None,
        calendar_model: str | None = None,
        precision: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        canonical_summary_id: UUID | None = None,
        session: Session | None = None,
    ) -> None:
        """Creates a new summary"""
        log.info(f"Creating a new summary: {text[:50]}...")
        summary = Summary(
            id=id,
            text=text,
            datetime=datetime,
            calendar_model=calendar_model,
            precision=precision,
            latitude=latitude,
            longitude=longitude,
            canonical_summary_id=canonical_summary_id,
        )
        if session:
            session.add(summary)
            session.flush()
        else:
            with Session(self._engine, future=True) as s:
                s.add(summary)
                s.commit()

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
        datetime: str,
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

    def get_story_order(
        self,
        tag_instances: list[TagInstanceWithTimeAndOrder],
        target: TagInstanceWithTime,
    ) -> int:
        BASE_INDEX = 100_000
        INTERVAL = 1_000
        if not tag_instances:  # base case
            return BASE_INDEX
        sorted_tag_instances = sorted(tag_instances, key=lambda tag: tag.story_order)
        target_date_tuple = (target.datetime, target.precision)
        tag_instances_by_date_tuples = defaultdict(list)
        for tag_instance in sorted_tag_instances:
            date_tuple = (tag_instance.datetime, tag_instance.precision)
            tag_instances_by_date_tuples[date_tuple].append(tag_instance)

        if target_date_tuple in tag_instances_by_date_tuples:
            # tag instance datetime and precision match all the instances in this list,
            # so find the earliest possible story_order that doesn't violate an ID in `after`
            after = target.after or set()

            tag_instance_subset = tag_instances_by_date_tuples[target_date_tuple]
            min_index_of_subset = -1  # keep track of lower limit
            for index, tag_instance in enumerate(tag_instance_subset):
                if tag_instance.summary_id in after:
                    min_index_of_subset = index
            if min_index_of_subset == -1:
                # index is less than the first index in this list, so we go back to the full
                # list to find the previous index
                current_index = sorted_tag_instances.index(tag_instance_subset[0])
                if current_index == 0:
                    return sorted_tag_instances[0].story_order - INTERVAL
                else:
                    return self.calculate_index(
                        min_index=sorted_tag_instances[current_index - 1].story_order,
                        max_index=sorted_tag_instances[current_index].story_order,
                    )
            elif min_index_of_subset + 1 == len(tag_instance_subset):
                # index is greater than the last index in this list,
                # so we go back to full list to find next index
                current_index = sorted_tag_instances.index(
                    tag_instance_subset[min_index_of_subset]
                )
                if current_index + 1 == len(sorted_tag_instances):  # last tag_instance
                    return sorted_tag_instances[current_index].story_order + INTERVAL
                return self.calculate_index(
                    min_index=sorted_tag_instances[current_index].story_order,
                    max_index=sorted_tag_instances[current_index + 1].story_order,
                )
            else:
                return self.calculate_index(
                    min_index=tag_instance_subset[min_index_of_subset].story_order,
                    max_index=tag_instance_subset[min_index_of_subset + 1].story_order,
                )

        # this tag instance has a unique datetime/precision combination, so
        # we find its order in the existing list.
        for index, tag_instance in enumerate(sorted_tag_instances):
            if tag_instance.datetime < target.datetime:
                continue
            elif (
                tag_instance.datetime == target.datetime
                and tag_instance.precision < target.precision
            ):
                continue
            else:
                if index == 0:  # base case
                    return tag_instance.story_order - INTERVAL
                return self.calculate_index(
                    min_index=sorted_tag_instances[index - 1].story_order,
                    max_index=tag_instance.story_order,
                )
        # this tag instance is later than all others
        return sorted_tag_instances[-1].story_order + INTERVAL

    def calculate_index(self, min_index: int, max_index: int):
        difference = max_index - min_index
        if difference == 1:
            raise RebalanceError
        # return an index approx halfway between the two existing indices
        return min_index + (difference // 2)

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
                limit 1
            """
            ),
            {
                "datetime": datetime,
                "calendar_model": calendar_model,
                "precision": precision,
            },
        ).scalar_one_or_none()

        return row

    def bulk_create_tag_instances(
        self,
        tag_instances: list[TagInstanceInput],
        after: list[UUID],
        session: Session,
    ) -> list[TagInstanceModel]:
        """Create multiple tag instances in a single operation for better performance."""
        # Group tag instances by tag_id for efficient story ordering
        instances_by_tag = defaultdict(list)
        for instance in tag_instances:
            instances_by_tag[instance.tag_id].append(instance)

        # Process each tag group
        result_instances = []

        for tag_id, instances in instances_by_tag.items():
            # Prepare all instances for this tag
            models = []
            values = []

            for i, instance in enumerate(instances):
                instance_id = uuid4()

                model = TagInstanceModel(
                    id=instance_id,
                    **instance.model_dump(),
                )
                models.append(model)

                values.append(model.model_dump())

            if values:
                placeholders = []
                all_params = {"after": json.dumps([str(id) for id in after])}

                for i, val in enumerate(values):
                    placeholder = f"(:id_{i}, :start_char_{i}, :stop_char_{i}, :summary_id_{i}, :tag_id_{i}, :story_order_{i}, :after)"
                    placeholders.append(placeholder)

                    for key, value in val.items():
                        all_params[f"{key}_{i}"] = value

                stmt = f"""
                    INSERT INTO tag_instances
                        (id, start_char, stop_char, summary_id, tag_id, story_order, after)
                    VALUES
                        {', '.join(placeholders)}
                """
                session.execute(text(stmt), all_params)

            result_instances.extend(models)

        return result_instances

    def update_null_story_order(self, tag_id: UUID, session: Session) -> None:
        """
        Updates all null story_order values for a given tag_id based on time ordering.

        This method:
        1. Finds all tag instances with null story_order for the given tag_id
        2. For each instance, determines the correct order using event datetime
        3. Updates all instances in a single database operation
        4. Uses a sparse integer approach for story_order values

        Args:
            tag_id: UUID of the tag to update story orders for
            session: SQLAlchemy session to use
        """
        # Serialize concurrent callers for the same tag_id. Without this,
        # multiple background tasks publishing events that share a tag (e.g.
        # the same place or person) can deadlock on tag_instances UPDATE.
        # pg_advisory_xact_lock is released automatically at transaction end.
        session.execute(
            text("SELECT pg_advisory_xact_lock(abs(hashtext(:tag_id_str)))"),
            {"tag_id_str": str(tag_id)},
        )

        tag_instances = session.execute(
            text(
                """
                SELECT 
                    tag_instances.id,
                    tag_instances.summary_id,
                    tag_instances.tag_id,
                    tag_instances.after,
                    tag_instances.story_order,
                    (
                        SELECT times.datetime
                        FROM summaries s
                        JOIN tag_instances ti ON ti.summary_id = s.id
                        JOIN tags t ON t.id = ti.tag_id AND t.type = 'TIME'
                        JOIN times ON times.id = t.id
                        WHERE s.id = tag_instances.summary_id
                        ORDER BY times.datetime, times.precision
                        LIMIT 1
                    ) AS datetime,
                    (
                        SELECT times.precision
                        FROM summaries s
                        JOIN tag_instances ti ON ti.summary_id = s.id
                        JOIN tags t ON t.id = ti.tag_id AND t.type = 'TIME'
                        JOIN times ON times.id = t.id
                        WHERE s.id = tag_instances.summary_id
                        ORDER BY times.datetime, times.precision
                        LIMIT 1
                    ) AS precision
                FROM tag_instances
                WHERE tag_instances.tag_id = :tag_id
                """
            ),
            {"tag_id": tag_id},
        ).all()
        nonnull_instances: list[TagInstanceWithTimeAndOrder] = []
        null_instances: list[TagInstanceWithTime] = []
        for row in tag_instances:
            if row.story_order is None:
                null_instances.append(
                    TagInstanceWithTime.model_validate(row, from_attributes=True)
                )
            else:
                nonnull_instances.append(
                    TagInstanceWithTimeAndOrder.model_validate(
                        row, from_attributes=True
                    )
                )

        if not null_instances:
            return

        instance_updates: list[dict[str, int]] = []
        for target in null_instances:
            try:
                story_order = self.get_story_order(
                    tag_instances=nonnull_instances,
                    target=target,
                )
            except RebalanceError:
                # commit current state so current calculations are included in the rebalance
                if instance_updates:
                    self._bulk_update_story_order(
                        instance_updates=instance_updates,
                        session=session,
                        tag_id=tag_id,
                    )
                raise
            instance_updates.append({"id": target.id, "story_order": story_order})
            # insert the new story into nonnull instances so its available for the next calculation
            new_nonnull_instance = TagInstanceWithTimeAndOrder.model_validate(
                {
                    **target.model_dump(),
                    "story_order": story_order,
                }
            )
            try:
                index = next(
                    i
                    for i, tag_instance in enumerate(nonnull_instances)
                    if tag_instance.story_order < story_order
                )
                nonnull_instances.insert(index, new_nonnull_instance)
            except StopIteration:  # story order belongs at the end
                nonnull_instances.append(new_nonnull_instance)

        # Update all instances in a single operation
        if instance_updates:
            self._bulk_update_story_order(
                instance_updates=instance_updates, session=session, tag_id=tag_id
            )

    def _bulk_update_story_order(
        self, instance_updates: list[dict[str, int]], session: Session, tag_id: UUID
    ):
        # Prepare the SQL for bulk update
        update_stmt = "UPDATE tag_instances SET story_order = CASE id "
        params = {"tag_id": tag_id}
        id_list = []
        for i, update in enumerate(instance_updates):
            update_stmt += f"WHEN :id_{i} THEN :order_{i} "
            params[f"id_{i}"] = update["id"]
            params[f"order_{i}"] = update["story_order"]
            id_list.append(f":id_{i}")
        update_stmt += (
            "ELSE story_order END WHERE tag_id = :tag_id AND id IN ("
            + ", ".join(id_list)
            + ")"
        )
        # Execute the update
        session.execute(text(update_stmt), params)
        session.commit()

    def rebalance_story_order(self, tag_id: UUID, session: Session) -> dict[UUID, int]:
        """Rebalances story_order values for a given tag_id.

        Takes all non-null story_order values for the given tag_id and updates them
        to maintain their relative ordering while ensuring exactly 1000 between each value.
        Null values are left untouched.

        Args:
            tag_id: UUID of the tag to rebalance story orders for
            session: SQLAlchemy session to use

        Returns:
            dict[UUID, int]: A dictionary mapping tag instance IDs to their new story order values
        """
        # Get all non-null story_order values for this tag, ordered
        rows = session.execute(
            text(
                """
                SELECT id, story_order
                FROM tag_instances 
                WHERE tag_id = :tag_id 
                AND story_order IS NOT NULL
                ORDER BY story_order ASC
                """
            ),
            {"tag_id": tag_id},
        ).all()

        if not rows:
            return {}

        # First set all story_orders to NULL to avoid unique constraint violations
        session.execute(
            text(
                """
                UPDATE tag_instances 
                SET story_order = NULL 
                WHERE tag_id = :tag_id 
                AND id IN (SELECT id FROM tag_instances WHERE tag_id = :tag_id AND story_order IS NOT NULL)
                """
            ),
            {"tag_id": tag_id},
        )

        # Calculate new story_order values with 1000 between each
        BASE_ORDER = 100_000  # Start at 100,000 to match existing pattern
        INTERVAL = 1_000

        updates = []
        result = {}
        for i, row in enumerate(rows):
            new_order = BASE_ORDER + (i * INTERVAL)
            updates.append({"id": row.id, "story_order": new_order})
            result[row.id] = new_order

        # Update all instances in a single operation
        if updates:
            update_stmt = "UPDATE tag_instances SET story_order = CASE id "
            params = {"tag_id": tag_id}
            id_list = []

            for i, update in enumerate(updates):
                update_stmt += f"WHEN :id_{i} THEN :order_{i} "
                params[f"id_{i}"] = update["id"]
                params[f"order_{i}"] = update["story_order"]
                id_list.append(f":id_{i}")

            update_stmt += (
                "ELSE story_order END WHERE tag_id = :tag_id AND id IN ("
                + ", ".join(id_list)
                + ")"
            )

            session.execute(text(update_stmt), params)
            session.commit()
        return result

    def get_nearby_events(
        self,
        event_id: UUID,
        calendar_model: str,
        precision: int,
        datetime_prefix: str,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        session: Session | None = None,
    ) -> list[NearbyEventRow]:
        """Find events near the given event based on time and location."""
        stmt = text(
            """
            SELECT DISTINCT
                s.id AS event_id,
                person_tag.id AS story_id,
                person_name.name AS person_name,
                sn.description AS person_description,
                s.text AS summary_text,
                place_name.name AS place_name,
                s.latitude,
                s.longitude,
                s.datetime,
                s.precision,
                s.calendar_model
            FROM summaries s
            -- join to person tag via tag_instances
            JOIN tag_instances person_ti ON person_ti.summary_id = s.id
            JOIN tags person_tag ON person_tag.id = person_ti.tag_id AND person_tag.type = 'PERSON'
            JOIN tag_names person_tn ON person_tn.tag_id = person_tag.id
            JOIN names person_name ON person_name.id = person_tn.name_id
            -- person description from story_names
            LEFT JOIN story_names sn ON sn.tag_id = person_tag.id
            -- join to place tag via tag_instances
            JOIN tag_instances place_ti ON place_ti.summary_id = s.id
            JOIN tags place_tag ON place_tag.id = place_ti.tag_id AND place_tag.type = 'PLACE'
            JOIN tag_names place_tn ON place_tn.tag_id = place_tag.id
            JOIN names place_name ON place_name.id = place_tn.name_id
            WHERE s.id != :event_id
                AND s.calendar_model = :calendar_model
                AND s.precision >= :precision
                AND s.datetime LIKE :datetime_prefix
                AND s.latitude BETWEEN :min_lat AND :max_lat
                AND s.longitude BETWEEN :min_lng AND :max_lng
        """
        )

        params = {
            "event_id": event_id,
            "calendar_model": calendar_model,
            "precision": precision,
            "datetime_prefix": datetime_prefix + "%",
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lng": min_lng,
            "max_lng": max_lng,
        }

        should_close = False
        if session is None:
            session = Session(self._engine, future=True)
            should_close = True

        try:
            rows = session.execute(stmt, params).all()
            return [
                NearbyEventRow(
                    event_id=row.event_id,
                    story_id=row.story_id,
                    person_name=row.person_name,
                    person_description=row.person_description,
                    summary_text=row.summary_text,
                    place_name=row.place_name,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    datetime=row.datetime,
                    precision=row.precision,
                    calendar_model=row.calendar_model,
                )
                for row in rows
            ]
        finally:
            if should_close:
                session.close()

    # --- Text Reader methods ---

    def search_tags_by_name_and_type(self, name: str, tag_type: str) -> list[dict]:
        """Fuzzy search tags by name filtered by type (PERSON, PLACE, TIME).

        Also returns description (from story_names) and earliest/latest summary
        dates (from tag_instances → summaries) to aid entity disambiguation.
        """
        if not name:
            return []
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    WITH matches AS (
                        SELECT DISTINCT
                            tags.id,
                            names.name,
                            tags.type,
                            similarity(names.name, :search_term) AS sim
                        FROM tags
                        JOIN tag_names ON tags.id = tag_names.tag_id
                        JOIN names ON names.id = tag_names.name_id
                        WHERE tags.type = :tag_type
                          AND (similarity(names.name, :search_term) > 0.3
                               OR names.name ILIKE :like_pattern)
                        ORDER BY sim DESC
                        LIMIT 20
                    )
                    SELECT
                        m.id,
                        m.name,
                        m.type,
                        m.sim,
                        (SELECT sn.description
                           FROM story_names sn
                          WHERE sn.tag_id = m.id
                            AND sn.description IS NOT NULL
                          LIMIT 1) AS description,
                        (SELECT MIN(s.datetime)
                           FROM tag_instances ti
                           JOIN summaries s ON s.id = ti.summary_id
                          WHERE ti.tag_id = m.id) AS earliest_date,
                        (SELECT MAX(s.datetime)
                           FROM tag_instances ti
                           JOIN summaries s ON s.id = ti.summary_id
                          WHERE ti.tag_id = m.id) AS latest_date
                    FROM matches m
                    ORDER BY m.sim DESC
                    """
                ),
                {
                    "tag_type": tag_type,
                    "search_term": name,
                    "like_pattern": f"%{name}%",
                },
            ).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "type": row.type,
                    "description": row.description,
                    "earliest_date": row.earliest_date,
                    "latest_date": row.latest_date,
                }
                for row in rows
            ]

    def search_places_by_name_and_coordinates(
        self,
        name: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float = 1.0,
    ) -> list[dict]:
        """Search places by name and/or coordinates."""
        results = []

        with Session(self._engine, future=True) as session:
            if name:
                rows = session.execute(
                    text(
                        """
                        SELECT DISTINCT
                            tags.id,
                            names.name,
                            places.latitude,
                            places.longitude,
                            similarity(names.name, :search_term) AS sim
                        FROM tags
                        JOIN tag_names ON tags.id = tag_names.tag_id
                        JOIN names ON names.id = tag_names.name_id
                        JOIN places ON places.id = tags.id
                        WHERE tags.type = 'PLACE'
                          AND (similarity(names.name, :search_term) > 0.3
                               OR names.name ILIKE :like_pattern)
                        ORDER BY sim DESC
                        LIMIT 50
                        """
                    ),
                    {
                        "search_term": name,
                        "like_pattern": f"%{name}%",
                    },
                ).all()
                results.extend(
                    [
                        {
                            "id": row.id,
                            "name": row.name,
                            "latitude": row.latitude,
                            "longitude": row.longitude,
                        }
                        for row in rows
                    ]
                )

            if latitude is not None and longitude is not None:
                rows = session.execute(
                    text(
                        """
                        SELECT DISTINCT
                            tags.id,
                            names.name,
                            places.latitude,
                            places.longitude
                        FROM tags
                        JOIN tag_names ON tags.id = tag_names.tag_id
                        JOIN names ON names.id = tag_names.name_id
                        JOIN places ON places.id = tags.id
                        WHERE tags.type = 'PLACE'
                          AND places.latitude BETWEEN :min_lat AND :max_lat
                          AND places.longitude BETWEEN :min_lng AND :max_lng
                        LIMIT 20
                        """
                    ),
                    {
                        "min_lat": latitude - radius,
                        "max_lat": latitude + radius,
                        "min_lng": longitude - radius,
                        "max_lng": longitude + radius,
                    },
                ).all()
                existing_ids = {r["id"] for r in results}
                results.extend(
                    [
                        {
                            "id": row.id,
                            "name": row.name,
                            "latitude": row.latitude,
                            "longitude": row.longitude,
                        }
                        for row in rows
                        if row.id not in existing_ids
                    ]
                )

        return results

    def find_matching_summary(
        self,
        person_ids: list[UUID],
        place_id: UUID,
        datetime_val: str,
        calendar_model: str,
        precision: int,
    ) -> dict | None:
        """Find a summary that matches the given person, place, and time."""
        with Session(self._engine, future=True) as session:
            # Find summaries that have tag_instances for ALL given person_ids and the place_id
            all_tag_ids = list(person_ids) + [place_id]
            row = session.execute(
                text(
                    """
                    SELECT s.id as summary_id, s.text as summary_text,
                           BOOL_OR(c.wikidata_item_id IS NOT NULL) as has_wikidata_citation
                    FROM summaries s
                    JOIN tag_instances ti ON ti.summary_id = s.id
                    LEFT JOIN citations c ON c.summary_id = s.id
                    WHERE s.datetime = :datetime_val
                      AND s.calendar_model = :calendar_model
                      AND s.precision = :precision
                      AND ti.tag_id = ANY(:tag_ids)
                    GROUP BY s.id, s.text
                    HAVING COUNT(DISTINCT ti.tag_id) = :tag_count
                    LIMIT 1
                    """
                ),
                {
                    "datetime_val": datetime_val,
                    "calendar_model": calendar_model,
                    "precision": precision,
                    "tag_ids": all_tag_ids,
                    "tag_count": len(all_tag_ids),
                },
            ).one_or_none()
            if row:
                return {
                    "summary_id": row.summary_id,
                    "summary_text": row.summary_text,
                    "has_wikidata_citation": row.has_wikidata_citation,
                }
            return None

    def create_text_reader_story(
        self,
        id: UUID,
        name: str,
        description: str | None = None,
        source_id: UUID | None = None,
    ) -> None:
        """Create a new text-reader story."""
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    INSERT INTO stories (id, name, description, source_id, created_at)
                    VALUES (:id, :name, :description, :source_id, now())
                    """
                ),
                {
                    "id": id,
                    "name": name,
                    "description": description,
                    "source_id": source_id,
                },
            )
            session.commit()

    def add_summary_to_story(
        self, story_id: UUID, summary_id: UUID, position: int
    ) -> None:
        """Add a summary to a text-reader story at a given position."""
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    INSERT INTO story_summaries (id, story_id, summary_id, position)
                    VALUES (:id, :story_id, :summary_id, :position)
                    """
                ),
                {
                    "id": uuid4(),
                    "story_id": story_id,
                    "summary_id": summary_id,
                    "position": position,
                },
            )
            session.commit()

    def get_story_by_source_id(self, source_id: UUID) -> dict | None:
        """Get a text-reader story by its source_id."""
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    SELECT id, name, description, source_id
                    FROM stories WHERE source_id = :source_id
                    LIMIT 1
                    """
                ),
                {"source_id": source_id},
            ).one_or_none()
            if row:
                return {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "source_id": row.source_id,
                }
            return None

    def get_next_story_position(self, story_id: UUID) -> int:
        """Get the next available position for a story."""
        with Session(self._engine, future=True) as session:
            max_pos = session.execute(
                text(
                    """
                    SELECT COALESCE(MAX(position), -1) + 1
                    FROM story_summaries WHERE story_id = :story_id
                    """
                ),
                {"story_id": story_id},
            ).scalar()
            return max_pos

    def update_summary_text(self, summary_id: UUID, new_text: str) -> None:
        """Update the text of an existing summary."""
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    UPDATE summaries SET text = :new_text
                    WHERE id = :summary_id
                    """
                ),
                {"summary_id": summary_id, "new_text": new_text},
            )
            session.commit()

    def add_citation_to_summary(
        self,
        summary_id: UUID,
        source_id: UUID,
        citation_text: str,
        page_num: int | None = None,
        access_date: str | None = None,
    ) -> UUID:
        """Add a new citation to an existing summary."""
        citation_id = uuid4()
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    INSERT INTO citations (id, text, source_id, summary_id, page_num, access_date)
                    VALUES (:id, :text, :source_id, :summary_id, :page_num, :access_date)
                    """
                ),
                {
                    "id": citation_id,
                    "text": citation_text,
                    "source_id": source_id,
                    "summary_id": summary_id,
                    "page_num": page_num,
                    "access_date": access_date,
                },
            )
            session.commit()
        return citation_id

    def create_source_with_session(
        self,
        id: UUID,
        title: str,
        author: str,
        publisher: str,
        pub_date: str | None,
        pdf_page_offset: int = 0,
    ) -> None:
        """Create a source and return immediately (no citation linking)."""
        with Session(self._engine, future=True) as session:
            source = Source(
                id=id,
                title=title,
                author=author,
                publisher=publisher,
                pub_date=pub_date,
                kwargs={},
                pdf_page_offset=pdf_page_offset,
            )
            session.add(source)
            session.commit()
            self._add_to_source_trie(source)

    # ------------------------------------------------------------------
    # Themes
    # ------------------------------------------------------------------

    def get_themes(self) -> list[ThemeWithChildrenModel]:
        """Return all themes, assembled into a parent→children hierarchy."""
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select id, name, slug, parent_id, display_order
                    from themes
                    order by display_order
                    """
                )
            ).fetchall()

        by_id: dict = {}
        children_by_parent: dict = {}
        for row in rows:
            by_id[str(row.id)] = row
            if row.parent_id is not None:
                children_by_parent.setdefault(str(row.parent_id), []).append(row)

        return [
            ThemeWithChildrenModel(
                id=row.id,
                name=row.name,
                slug=row.slug,
                parent_id=row.parent_id,
                display_order=row.display_order,
                children=[
                    ThemeModel(
                        id=child.id,
                        name=child.name,
                        slug=child.slug,
                        parent_id=child.parent_id,
                        display_order=child.display_order,
                    )
                    for child in children_by_parent.get(str(row.id), [])
                ],
            )
            for row in rows
            if row.parent_id is None
        ]

    def get_theme_by_slug(self, slug: str) -> ThemeModel | None:
        """Return a single theme by slug, or None if not found."""
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    select id, name, slug, parent_id, display_order
                    from themes
                    where slug = :slug
                    """
                ),
                {"slug": slug},
            ).one_or_none()
        if row is None:
            return None
        return ThemeModel(
            id=row.id,
            name=row.name,
            slug=row.slug,
            parent_id=row.parent_id,
            display_order=row.display_order,
        )

    def get_themes_for_summary(self, summary_id: UUID) -> list[SummaryThemeModel]:
        """Return all theme associations for a given summary."""
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select id, summary_id, theme_id, is_primary, confidence
                    from summary_themes
                    where summary_id = :summary_id
                    """
                ),
                {"summary_id": summary_id},
            ).fetchall()
        return [
            SummaryThemeModel(
                id=row.id,
                summary_id=row.summary_id,
                theme_id=row.theme_id,
                is_primary=row.is_primary,
                confidence=row.confidence,
            )
            for row in rows
        ]

    def add_summary_theme(
        self,
        summary_id: UUID,
        theme_id: UUID,
        is_primary: bool,
        confidence: float | None = None,
    ) -> SummaryThemeModel:
        """Associate a theme with a summary. Raises if the pair already exists."""
        association_id = uuid4()
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    insert into summary_themes (id, summary_id, theme_id, is_primary, confidence)
                    values (:id, :summary_id, :theme_id, :is_primary, :confidence)
                    """
                ),
                {
                    "id": association_id,
                    "summary_id": summary_id,
                    "theme_id": theme_id,
                    "is_primary": is_primary,
                    "confidence": confidence,
                },
            )
            session.commit()
        return SummaryThemeModel(
            id=association_id,
            summary_id=summary_id,
            theme_id=theme_id,
            is_primary=is_primary,
            confidence=confidence,
        )

    # -----------------------------------------------------------------------
    # User engagement: favorites, views
    # -----------------------------------------------------------------------

    def add_favorite(self, user_id: str, summary_id: UUID) -> None:
        """Add a favorite. Idempotent — does nothing if already favorited."""
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    insert into user_favorites (user_id, summary_id, created_at)
                    values (:user_id, :summary_id, now())
                    on conflict (user_id, summary_id) do nothing
                    """
                ),
                {"user_id": user_id, "summary_id": summary_id},
            )
            session.commit()

    def remove_favorite(self, user_id: str, summary_id: UUID) -> None:
        """Remove a favorite. Idempotent — does nothing if not favorited."""
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    delete from user_favorites
                    where user_id = :user_id and summary_id = :summary_id
                    """
                ),
                {"user_id": user_id, "summary_id": summary_id},
            )
            session.commit()

    def get_favorites(self, user_id: str) -> list[dict]:
        """Return all favorites for a user, with summary text."""
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select uf.summary_id, s.text as summary_text,
                           uf.created_at::text as created_at
                    from user_favorites uf
                    join summaries s on s.id = uf.summary_id
                    where uf.user_id = :user_id
                    order by uf.created_at desc
                    """
                ),
                {"user_id": user_id},
            ).all()
        return [
            {
                "summary_id": row.summary_id,
                "summary_text": row.summary_text,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def record_view(self, user_id: str, summary_id: UUID) -> None:
        """Record that a user viewed an event."""
        view_id = uuid4()
        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    insert into user_events (id, user_id, summary_id, event_type, created_at)
                    values (:id, :user_id, :summary_id, 'view', now())
                    """
                ),
                {
                    "id": view_id,
                    "user_id": user_id,
                    "summary_id": summary_id,
                },
            )
            session.commit()

    # -----------------------------------------------------------------------
    # Feed
    # -----------------------------------------------------------------------

    def get_feed(
        self,
        limit: int = 20,
        theme_slugs: list[str] | None = None,
        after_cursor: str | None = None,
        user_id: str | None = None,
    ) -> list[dict]:
        """Return a paginated, theme-diverse feed of events.

        Interleaves events across primary themes using ROW_NUMBER
        partitioned by theme, so the feed doesn't cluster one theme.
        """
        params: dict = {"limit": limit}
        theme_filter = ""
        cursor_filter = ""
        fav_join = ""
        fav_select = "false as is_favorited"

        if theme_slugs:
            theme_filter = (
                "join summary_themes st_filter "
                "  on st_filter.summary_id = s.id and st_filter.is_primary = true "
                "join themes t_filter "
                "  on t_filter.id = st_filter.theme_id and t_filter.slug = any(:theme_slugs) "
            )
            params["theme_slugs"] = theme_slugs

        if after_cursor:
            # cursor format: "row_num:summary_id"
            parts = after_cursor.split(":", 1)
            if len(parts) == 2:
                cursor_filter = (
                    "where (interleave_rank > :cursor_rank "
                    "   or (interleave_rank = :cursor_rank and s_id > :cursor_id))"
                )
                params["cursor_rank"] = int(parts[0])
                params["cursor_id"] = parts[1]

        if user_id:
            fav_join = (
                "left join user_favorites uf "
                "  on uf.summary_id = ranked.s_id and uf.user_id = :user_id "
            )
            fav_select = "uf.user_id is not null as is_favorited"
            params["user_id"] = user_id

        query = f"""
            with ranked as (
                select
                    s.id as s_id,
                    s.text as s_text,
                    s.latitude,
                    s.longitude,
                    s.datetime,
                    s.precision,
                    coalesce(pt.slug, 'untagged') as primary_theme_slug,
                    row_number() over (
                        partition by coalesce(pt.slug, 'untagged')
                        order by s.id
                    ) as theme_rank
                from summaries s
                left join summary_themes st_primary
                    on st_primary.summary_id = s.id and st_primary.is_primary = true
                left join themes pt on pt.id = st_primary.theme_id
                {theme_filter}
            ),
            interleaved as (
                select *,
                    row_number() over (
                        order by theme_rank, primary_theme_slug, s_id
                    ) as interleave_rank
                from ranked
            )
            select
                interleaved.s_id,
                interleaved.s_text,
                interleaved.latitude,
                interleaved.longitude,
                interleaved.datetime,
                interleaved.precision,
                interleaved.interleave_rank,
                {fav_select}
            from interleaved
            {fav_join}
            {cursor_filter}
            order by interleaved.interleave_rank, interleaved.s_id
            limit :limit
        """

        with Session(self._engine, future=True) as session:
            rows = session.execute(text(query), params).all()

        results = []
        for row in rows:
            results.append(
                {
                    "summary_id": row.s_id,
                    "summary_text": row.s_text,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "datetime": row.datetime,
                    "precision": row.precision,
                    "interleave_rank": row.interleave_rank,
                    "is_favorited": row.is_favorited,
                }
            )
        return results

    def get_feed_tags(self, summary_ids: list[UUID]) -> dict[UUID, list[dict]]:
        """Batch-fetch tags for a list of summary IDs."""
        if not summary_ids:
            return {}
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select ti.summary_id, t.id as tag_id, t.type, t.name
                    from tag_instances ti
                    join tags t on t.id = ti.tag_id
                    where ti.summary_id = any(:ids)
                    """
                ),
                {"ids": summary_ids},
            ).all()
        result: dict[UUID, list[dict]] = {sid: [] for sid in summary_ids}
        for row in rows:
            result[row.summary_id].append(
                {"id": row.tag_id, "type": row.type, "name": row.name}
            )
        return result

    def get_feed_themes(
        self, summary_ids: list[UUID]
    ) -> dict[UUID, list[dict]]:
        """Batch-fetch themes for a list of summary IDs."""
        if not summary_ids:
            return {}
        with Session(self._engine, future=True) as session:
            rows = session.execute(
                text(
                    """
                    select st.summary_id, t.slug, t.name
                    from summary_themes st
                    join themes t on t.id = st.theme_id
                    where st.summary_id = any(:ids)
                    order by st.is_primary desc
                    """
                ),
                {"ids": summary_ids},
            ).all()
        result: dict[UUID, list[dict]] = {sid: [] for sid in summary_ids}
        for row in rows:
            result[row.summary_id].append(
                {"slug": row.slug, "name": row.name}
            )
        return result
