import logging
from typing import Literal
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor
from math import ceil
import threading

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.core import (
    PersonInput,
    Person,
    PlaceInput,
    Place,
    TimeInput,
    Time,
    TagPointer,
    CitationInput,
    TagInstance,
    Story,
    StoryPointer,
    StoryName,
    Map,
    Point,
    Tag,
    HistoryEvent,
    CalendarDate,
    Source,
)

from the_history_atlas.apps.config import Config
from the_history_atlas.apps.domain.models.history.tables import TagInstanceModel
from the_history_atlas.apps.domain.models.history.tables.tag_instance import (
    TagInstanceInput,
)
from the_history_atlas.apps.history.repository import Repository, RebalanceError
from the_history_atlas.apps.history.errors import (
    TagExistsError,
    MissingResourceError,
    DuplicateEventError,
)
from the_history_atlas.apps.history.trie import Trie

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class HistoryApp:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        source_trie = Trie()

        repository = Repository(
            database_client=database_client,
            source_trie=source_trie,
        )
        self._repository = repository
        self._source_trie = source_trie.build(
            entity_tuples=repository.get_all_source_titles_and_authors()
        )

    def prime_cache(self, cache_size=100):
        """Prime the default story and event cache"""
        self._repository.prime_default_story_cache(cache_size=cache_size)

    def start_cache_refresh(self, refresh_interval_seconds=3600):
        """Start the background cache refresh thread"""
        self._repository.start_cache_refresh_thread(
            refresh_interval_seconds=refresh_interval_seconds
        )

    def stop_cache_refresh(self):
        """Stop the background cache refresh thread"""
        self._repository.stop_cache_refresh_thread()

    def create_person(self, person: PersonInput) -> Person:
        if self._repository.get_tag_id_by_wikidata_id(wikidata_id=person.wikidata_id):
            raise TagExistsError(
                f"Person with wikidata id {person.wikidata_id} already exists."
            )
        id = uuid4()
        with self._repository.Session() as session:
            self._repository.create_person(
                id=id,
                session=session,
                wikidata_id=person.wikidata_id,
                wikidata_url=person.wikidata_url,
            )
            self._repository.add_name_to_tag(
                name=person.name, tag_id=id, session=session
            )
            self._repository.update_entity_trie(
                new_string=person.name, new_string_guid=str(id)
            )
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_person_story_names(person=person),
            )
            session.commit()
        return Person(id=id, **person.model_dump())

    def create_place(self, place: PlaceInput) -> Place:
        if self._repository.get_tag_id_by_wikidata_id(wikidata_id=place.wikidata_id):
            raise TagExistsError(
                f"Place with wikidata id {place.wikidata_id} already exists."
            )
        id = uuid4()
        with self._repository.Session() as session:
            self._repository.create_place(
                id=id,
                session=session,
                wikidata_id=place.wikidata_id,
                wikidata_url=place.wikidata_url,
                latitude=place.latitude,
                longitude=place.longitude,
            )
            self._repository.add_name_to_tag(
                name=place.name, tag_id=id, session=session
            )
            self._repository.update_entity_trie(
                new_string=place.name, new_string_guid=str(id)
            )
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_place_story_names(place=place),
            )
            session.commit()
        return Place(id=id, **place.model_dump())

    def create_time(self, time: TimeInput) -> Time:
        if self._repository.get_tag_id_by_wikidata_id(wikidata_id=time.wikidata_id):
            raise TagExistsError(
                f"Place with wikidata id {time.wikidata_id} already exists."
            )
        id = uuid4()
        with self._repository.Session() as session:
            self._repository.create_time(
                id=id,
                session=session,
                wikidata_id=time.wikidata_id,
                wikidata_url=time.wikidata_url,
                datetime=time.date,
                calendar_model=time.calendar_model,
                precision=time.precision,
            )
            self._repository.add_name_to_tag(name=time.name, tag_id=id, session=session)
            self._repository.update_entity_trie(
                new_string=time.name, new_string_guid=str(id)
            )
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_time_story_names(time=time),
            )
            session.commit()
        return Time(id=id, **time.model_dump())

    def get_tags_by_wikidata_ids(self, ids: list[str]) -> list[TagPointer]:
        return self._repository.get_tags_by_wikidata_ids(wikidata_ids=ids)

    def fuzzy_search_stories(self, search_string: str) -> list[dict[str, str]]:
        """
        Search for stories that match the given search string.
        Returns a list of dicts containing story IDs and names.
        Text-reader stories are returned first and preferred over wikidata stories
        when both match equivalently.
        """
        # Text-reader stories (stories table) — preferred
        text_reader_results = self._repository.search_stories_by_name(search_string)

        # Wikidata stories (names/tags tables)
        matches = self._repository.get_name_by_fuzzy_search(search_string)
        wikidata_results: list[dict] = []
        if matches:
            all_ids: set = set()
            for match in matches:
                all_ids.update(match.ids)
            with self._repository.Session() as session:
                story_names = self._repository.get_story_names(tuple(all_ids), session)
            wikidata_results = [
                {
                    "id": str(story_id),
                    "name": story_info["name"],
                    "description": story_info["description"],
                    "earliestYear": story_info["earliest_year"],
                    "latestYear": story_info["latest_year"],
                }
                for story_id, story_info in story_names.items()
            ]

        # Merge: text-reader first, then wikidata — deduplicate by normalised name
        seen_names: set[str] = set()
        merged: list[dict] = []
        for result in text_reader_results:
            key = result["name"].lower().strip()
            seen_names.add(key)
            merged.append(result)
        for result in wikidata_results:
            key = result["name"].lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                merged.append(result)
        return merged

    def create_wikidata_event(
        self,
        text: str,
        tags: list[TagInstance],
        citation: CitationInput,
        after: list[UUID],
    ):
        source = self._repository.get_source_by_title(title="Wikidata")
        if source:
            source_id = UUID(source.id)
        else:
            source_id = uuid4()
            self._repository.create_source(
                id=source_id,
                title="Wikidata",
                author="Wikidata Contributors",
                publisher="Wikimedia Foundation",
                pub_date=None,
            )
        summary_id = uuid4()

        with self._repository.Session() as session:
            # Look up time and place data from tag IDs for denormalized summary fields
            tag_ids = [tag.id for tag in tags]
            time_data = self._resolve_time_data(tag_ids, session)
            place_data = self._resolve_place_data(tag_ids, session)

            try:
                self._repository.create_summary(
                    id=summary_id,
                    text=text,
                    datetime=time_data.get("datetime"),
                    calendar_model=time_data.get("calendar_model"),
                    precision=time_data.get("precision"),
                    latitude=place_data.get("latitude"),
                    longitude=place_data.get("longitude"),
                    session=session,
                )
            except IntegrityError:
                raise DuplicateEventError

            citation_text = f"Wikidata. ({citation.access_date}). {citation.wikidata_item_title} ({citation.wikidata_item_id}). Wikimedia Foundation. {citation.wikidata_item_url}"
            citation_id = uuid4()
            # Use the optimized citation creation method that handles all relationships
            self._repository.create_citation_complete(
                id=citation_id,
                session=session,
                citation_text=citation_text,
                source_id=source_id,
                summary_id=summary_id,
                access_date=str(citation.access_date),
            )

            # Convert tags to dictionaries for bulk processing
            tag_instances = [
                TagInstanceInput(
                    start_char=tag.start_char,
                    stop_char=tag.stop_char,
                    summary_id=summary_id,
                    tag_id=tag.id,
                )
                for tag in tags
            ]

            # Use the bulk operation instead of individual inserts
            self._repository.bulk_create_tag_instances(
                tag_instances=tag_instances,
                after=after,
                session=session,
            )

            session.commit()

        return summary_id

    def _resolve_tag_types(self, tag_ids: list[UUID], session: Session) -> set[str]:
        """Look up the set of tag types present among the given tag IDs."""
        from sqlalchemy import text

        if not tag_ids:
            return set()
        stmt = text(
            """
            SELECT DISTINCT t.type
            FROM tags t
            WHERE t.id = ANY(:tag_ids)
        """
        )
        rows = session.execute(stmt, {"tag_ids": tag_ids}).fetchall()
        return {row[0] for row in rows}

    def _resolve_time_data(self, tag_ids: list[UUID], session: Session) -> dict:
        """Look up time data from tag IDs for denormalized summary fields."""
        from sqlalchemy import text

        if not tag_ids:
            return {}
        stmt = text(
            """
            SELECT t.datetime, t.calendar_model, t.precision
            FROM times t
            WHERE t.id = ANY(:tag_ids)
            LIMIT 1
        """
        )
        row = session.execute(stmt, {"tag_ids": tag_ids}).first()
        if row:
            return {
                "datetime": row[0],
                "calendar_model": row[1],
                "precision": row[2],
            }
        return {}

    def _resolve_place_data(self, tag_ids: list[UUID], session: Session) -> dict:
        """Look up place data from tag IDs for denormalized summary fields."""
        from sqlalchemy import text

        if not tag_ids:
            return {}
        stmt = text(
            """
            SELECT p.latitude, p.longitude
            FROM places p
            WHERE p.id = ANY(:tag_ids)
            LIMIT 1
        """
        )
        row = session.execute(stmt, {"tag_ids": tag_ids}).first()
        if row:
            return {
                "latitude": row[0],
                "longitude": row[1],
            }
        return {}

    def calculate_story_order(
        self,
        tag_ids: list[UUID],
        session: Session | None = None,
    ) -> None:
        """Calculate story order for any tag_instances which have not yet been ordered."""
        session_created = False
        if not session:
            session = Session(self._repository._engine, future=True)
            session_created = True

        try:
            for tag_id in tag_ids:
                try:
                    self._repository.update_null_story_order(
                        tag_id=tag_id, session=session
                    )
                except RebalanceError:
                    log.info(f"Rebalancing story order for story {tag_id}.")
                    self._repository.rebalance_story_order(
                        tag_id=tag_id, session=session
                    )
        finally:
            if session_created:
                session.close()

    def calculate_story_order_range(
        self,
        start_tag_id: UUID | None = None,
        stop_tag_id: UUID | None = None,
        num_workers: int = 1,
    ) -> None:
        """
        Calculate story order for tag_instances within the specified tag ID range.

        Args:
            start_tag_id: Optional UUID to start processing from (inclusive)
            stop_tag_id: Optional UUID to stop processing at (inclusive)
            num_workers: Number of threads to use for parallel processing
        """
        # Get all tag IDs that need processing within the range
        with self._repository.Session() as session:
            tag_ids = self._repository.get_tag_ids_with_null_orders(
                start_tag_id=start_tag_id, stop_tag_id=stop_tag_id, session=session
            )

            if not tag_ids:
                log.info(
                    "No tag IDs with null story orders found in the specified range."
                )
                return

            log.info(f"Processing {len(tag_ids)} tag IDs with {num_workers} workers")

            if num_workers <= 1:
                # Single-threaded mode
                self.calculate_story_order(tag_ids=tag_ids, session=session)
                return

        # Divide work among workers
        chunk_size = ceil(len(tag_ids) / num_workers)
        chunks = [
            tag_ids[i : i + chunk_size] for i in range(0, len(tag_ids), chunk_size)
        ]

        # Define worker function that will run in each thread
        def worker(chunk):
            thread_name = threading.current_thread().name
            log.info(f"{thread_name} processing {len(chunk)} tag IDs")

            # Create a new session for this thread
            with self._repository.Session() as session:
                self.calculate_story_order(tag_ids=chunk, session=session)

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            executor.map(worker, chunks)

    def get_story_pointers(
        self,
        event_id: UUID,
        story_id: UUID,
        direction: Literal["next", "prev"] | None,
        session: Session,
    ) -> list[StoryPointer]:
        match direction:
            case "next":
                return self.get_next_story_pointers(
                    event_id=event_id,
                    story_id=story_id,
                    session=session,
                )
            case "prev":
                return self.get_prev_story_pointers(
                    event_id=event_id,
                    story_id=story_id,
                    session=session,
                )
            case _:
                prev_pointers = self.get_prev_story_pointers(
                    event_id=event_id,
                    story_id=story_id,
                    session=session,
                )
                queried_event = [
                    StoryPointer(
                        story_id=story_id,
                        event_id=event_id,
                    )
                ]
                next_pointers = self.get_next_story_pointers(
                    event_id=event_id,
                    story_id=story_id,
                    session=session,
                )
                return prev_pointers + queried_event + next_pointers

    def get_next_story_pointers(
        self, event_id: UUID, story_id: UUID, session: Session
    ) -> list[StoryPointer]:
        DIRECTION: Literal["next"] = "next"
        story_pointers = self._repository.get_story_pointers(
            summary_id=event_id,
            tag_id=story_id,
            direction=DIRECTION,
            session=session,
        )
        while len(story_pointers) < 10:
            if not len(story_pointers):
                last_story_pointer = StoryPointer(event_id=event_id, story_id=story_id)
            else:
                last_story_pointer = story_pointers[-1]
            related_story = self._repository.get_related_story(
                summary_id=last_story_pointer.event_id,
                tag_id=last_story_pointer.story_id,
                direction=DIRECTION,
                session=session,
            )
            if not related_story:
                break
            related_story_pointers = self._repository.get_story_pointers(
                summary_id=related_story.event_id,
                tag_id=related_story.story_id,
                direction=DIRECTION,
                session=session,
            )
            story_pointers.append(related_story)
            story_pointers.extend(related_story_pointers)
        return story_pointers

    def get_prev_story_pointers(
        self, event_id: UUID, story_id: UUID, session: Session
    ) -> list[StoryPointer]:
        DIRECTION: Literal["prev"] = "prev"
        story_pointers = self._repository.get_story_pointers(
            summary_id=event_id,
            tag_id=story_id,
            direction=DIRECTION,
            session=session,
        )
        while len(story_pointers) < 10:
            if not len(story_pointers):
                last_story_pointer = StoryPointer(event_id=event_id, story_id=story_id)
            else:
                last_story_pointer = story_pointers[0]
            related_story = self._repository.get_related_story(
                summary_id=last_story_pointer.event_id,
                tag_id=last_story_pointer.story_id,
                direction=DIRECTION,
                session=session,
            )
            if not related_story:
                break
            related_story_pointers = self._repository.get_story_pointers(
                summary_id=related_story.event_id,
                tag_id=related_story.story_id,
                direction=DIRECTION,
                session=session,
            )
            story_pointers = [*related_story_pointers, related_story, *story_pointers]
        return story_pointers

    def get_story_list(
        self, event_id: UUID, story_id: UUID, direction: Literal["next", "prev"] | None
    ) -> Story:
        with self._repository.Session() as session:
            if self._repository.is_text_reader_story(story_id, session):
                if direction is None:
                    prev_pointers = self._repository.get_text_reader_story_pointers(
                        story_id=story_id,
                        summary_id=event_id,
                        direction="prev",
                        session=session,
                    )
                    next_pointers = self._repository.get_text_reader_story_pointers(
                        story_id=story_id,
                        summary_id=event_id,
                        direction="next",
                        session=session,
                    )
                    story_pointers = (
                        prev_pointers
                        + [StoryPointer(story_id=story_id, event_id=event_id)]
                        + next_pointers
                    )
                else:
                    story_pointers = self._repository.get_text_reader_story_pointers(
                        story_id=story_id,
                        summary_id=event_id,
                        direction=direction,
                        session=session,
                    )
            else:
                story_pointers = self.get_story_pointers(
                    event_id=event_id,
                    story_id=story_id,
                    direction=direction,
                    session=session,
                )
            events = self._repository.get_events(
                event_ids=tuple([story.event_id for story in story_pointers]),
                session=session,
            )
            story_names = self._repository.get_story_names(
                story_ids=tuple(
                    {
                        *[story_pointer.story_id for story_pointer in story_pointers],
                        story_id,
                    }
                ),
                session=session,
            )

        if not story_names:
            raise MissingResourceError("Story not found")
        story_names_by_event_id = {
            story_pointer.event_id: {
                "name": story_names[story_pointer.story_id]["name"],
                "description": story_names[story_pointer.story_id]["description"],
            }
            for story_pointer in story_pointers
        }

        history_events = [
            HistoryEvent(
                id=event_query.event_id,
                text=event_query.event_row.text,
                lang="en",
                date=CalendarDate(
                    datetime=event_query.calendar_date.datetime,
                    calendar=event_query.calendar_date.calendar_model,
                    precision=event_query.calendar_date.precision,
                ),
                source=Source(
                    id=event_query.event_row.source_id,
                    text=event_query.event_row.source_text,
                    title=event_query.event_row.source_title,
                    author=event_query.event_row.source_author,
                    publisher=event_query.event_row.source_publisher,
                    pub_date=event_query.event_row.source_access_date,
                ),
                tags=[
                    Tag(
                        id=tag.tag_id,
                        type=tag.type,
                        start_char=tag.start_char,
                        stop_char=tag.stop_char,
                        name=event_query.names[tag.tag_id].names[
                            0
                        ],  # take first name for now
                        default_story_id=tag.tag_id,
                    )
                    for tag in event_query.tags
                ],
                map=Map(
                    locations=[
                        Point(
                            id=event_query.location_row.tag_id,
                            latitude=event_query.location_row.latitude,
                            longitude=event_query.location_row.longitude,
                            name=event_query.names[
                                event_query.location_row.tag_id
                            ].names[0],
                        )
                    ]
                ),
                focus=event_id,
                story_title=story_names_by_event_id[event_query.event_id]["name"],
                description=story_names_by_event_id[event_query.event_id][
                    "description"
                ],
                stories=list(),  # todo
            )
            for event_query in events
        ]
        return Story(
            id=story_id,
            events=history_events,
            name=story_names[story_id]["name"],
        )

    def get_default_story_and_event(
        self,
        story_id: UUID | None,
        event_id: UUID | None,
    ) -> StoryPointer:
        if story_id:
            # get the first story
            return self._repository.get_default_event_by_story(story_id=story_id)
        elif event_id:
            # get the person story associated with this event
            return self._repository.get_default_story_by_event(event_id=event_id)
        else:
            # return random story/event
            return self._repository.get_default_story_and_event()

    def get_available_person_story_names(self, person: PersonInput) -> list[StoryName]:
        return [
            StoryName(
                lang="en",
                name=f"The Life of {person.name}",
                description=person.description,
            ),
        ]

    def get_available_place_story_names(self, place: PlaceInput) -> list[StoryName]:
        return [
            StoryName(
                lang="en",
                name=f"The History of {place.name}",
                description=place.description,
            ),
        ]

    def get_available_time_story_names(self, time: TimeInput) -> list[StoryName]:
        return [
            StoryName(
                lang="en",
                name=f"Events of {time.name}",
                description=time.description,
            ),
        ]

    # Precision → datetime prefix length mapping
    # 6=millennium(2), 7=century(3), 8=decade(4), 9=year(5), 10=month(8), 11=day(11)
    PRECISION_TO_PREFIX_LENGTH = {
        6: 2,
        7: 3,
        8: 4,
        9: 5,
        10: 8,
        11: 11,
    }

    MIN_NEARBY_PRECISION = 9

    def get_nearby_events(
        self,
        event_id: UUID,
        calendar_model: str,
        precision: int,
        datetime: str,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
    ):
        """Find events near the given event based on time prefix and spatial bounds.

        If no results are found, reduces precision by 1 (broadening the time window)
        and retries until precision reaches MIN_NEARBY_PRECISION (year), at which
        point results are returned regardless.
        """
        current_precision = precision
        while True:
            prefix_length = self.PRECISION_TO_PREFIX_LENGTH.get(current_precision, 5)
            datetime_prefix = datetime[:prefix_length]
            results = self._repository.get_nearby_events(
                event_id=event_id,
                calendar_model=calendar_model,
                precision=current_precision,
                datetime_prefix=datetime_prefix,
                min_lat=min_lat,
                max_lat=max_lat,
                min_lng=min_lng,
                max_lng=max_lng,
            )
            if results or current_precision <= self.MIN_NEARBY_PRECISION:
                return results
            current_precision -= 1

    # --- Text Reader methods ---

    def create_person_without_wikidata(
        self, name: str, description: str | None = None
    ) -> dict:
        """Create a person tag without wikidata_id."""
        id = uuid4()
        with self._repository.Session() as session:
            self._repository.create_person(
                id=id, session=session, wikidata_id=None, wikidata_url=None
            )
            self._repository.add_name_to_tag(name=name, tag_id=id, session=session)
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=[
                    StoryName(
                        lang="en",
                        name=f"The Life of {name}",
                        description=description,
                    )
                ],
            )
            session.commit()
        return {"id": id, "name": name, "description": description}

    def create_place_without_wikidata(
        self,
        name: str,
        latitude: float,
        longitude: float,
        geonames_id: int | None = None,
        description: str | None = None,
    ) -> dict:
        """Create a place tag without wikidata_id."""
        id = uuid4()
        with self._repository.Session() as session:
            self._repository.create_place(
                id=id,
                session=session,
                wikidata_id=None,
                wikidata_url=None,
                latitude=latitude,
                longitude=longitude,
            )
            self._repository.add_name_to_tag(name=name, tag_id=id, session=session)
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=[
                    StoryName(
                        lang="en",
                        name=f"The History of {name}",
                        description=description,
                    )
                ],
            )
            session.commit()
        return {
            "id": id,
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "geonames_id": geonames_id,
            "description": description,
        }

    def create_time_without_wikidata(
        self,
        name: str,
        date: str,
        calendar_model: str,
        precision: int,
        description: str | None = None,
    ) -> dict:
        """Get or create a time tag without wikidata_id."""
        with self._repository.Session() as session:
            existing_id = self._repository.time_exists(
                datetime=date,
                calendar_model=calendar_model,
                precision=precision,
                session=session,
            )
            if existing_id:
                return {
                    "id": existing_id,
                    "name": name,
                    "date": date,
                    "calendar_model": calendar_model,
                    "precision": precision,
                    "description": description,
                }
            id = uuid4()
            self._repository.create_time(
                id=id,
                session=session,
                datetime=date,
                calendar_model=calendar_model,
                precision=precision,
                wikidata_id=None,
                wikidata_url=None,
            )
            self._repository.add_name_to_tag(name=name, tag_id=id, session=session)
            self._repository.add_story_names(
                tag_id=id,
                session=session,
                story_names=[
                    StoryName(
                        lang="en",
                        name=f"Events of {name}",
                        description=description,
                    )
                ],
            )
            session.commit()
        return {
            "id": id,
            "name": name,
            "date": date,
            "calendar_model": calendar_model,
            "precision": precision,
            "description": description,
        }

    def create_text_reader_source(
        self,
        title: str,
        author: str,
        publisher: str,
        pub_date: str | None,
        pdf_page_offset: int = 0,
    ) -> dict:
        """Create a source for a text reader import."""
        source = self._repository.get_source_by_title(title=title)
        if source:
            return {
                "id": UUID(source.id),
                "title": source.title,
                "author": source.author,
                "publisher": source.publisher,
                "pub_date": source.pub_date,
                "pdf_page_offset": getattr(source, "pdf_page_offset", 0),
            }
        id = uuid4()
        self._repository.create_source_with_session(
            id=id,
            title=title,
            author=author,
            publisher=publisher,
            pub_date=pub_date,
            pdf_page_offset=pdf_page_offset,
        )
        return {
            "id": id,
            "title": title,
            "author": author,
            "publisher": publisher,
            "pub_date": pub_date,
            "pdf_page_offset": pdf_page_offset,
        }

    def create_text_reader_event(
        self,
        text: str,
        tags: list[TagInstance],
        citation_text: str,
        citation_page_num: int | None,
        citation_access_date: str | None,
        source_id: UUID,
        story_id: UUID,
        canonical_summary_id: UUID | None = None,
        theme_slugs: list[str] | None = None,
    ) -> UUID:
        """Create an event from the text reader pipeline."""
        summary_id = uuid4()

        with self._repository.Session() as session:
            tag_ids = [tag.id for tag in tags]

            # Validate that all three entity types are present
            tag_types = self._resolve_tag_types(tag_ids, session)
            missing_types = {"PERSON", "PLACE", "TIME"} - tag_types
            if missing_types:
                from the_history_atlas.apps.history.errors import MissingTagTypesError

                raise MissingTagTypesError(missing_types)

            time_data = self._resolve_time_data(tag_ids, session)
            place_data = self._resolve_place_data(tag_ids, session)

            try:
                self._repository.create_summary(
                    id=summary_id,
                    text=text,
                    datetime=time_data.get("datetime"),
                    calendar_model=time_data.get("calendar_model"),
                    precision=time_data.get("precision"),
                    latitude=place_data.get("latitude"),
                    longitude=place_data.get("longitude"),
                    canonical_summary_id=canonical_summary_id,
                    session=session,
                )
            except IntegrityError:
                raise DuplicateEventError

            citation_id = uuid4()
            self._repository.create_citation_complete(
                id=citation_id,
                session=session,
                citation_text=citation_text,
                source_id=source_id,
                summary_id=summary_id,
                page_num=citation_page_num,
                access_date=citation_access_date,
            )

            tag_instances = [
                TagInstanceInput(
                    start_char=tag.start_char,
                    stop_char=tag.stop_char,
                    summary_id=summary_id,
                    tag_id=tag.id,
                )
                for tag in tags
            ]
            self._repository.bulk_create_tag_instances(
                tag_instances=tag_instances,
                after=[],
                session=session,
            )
            session.commit()

        # Add to text-reader story
        position = self._repository.get_next_story_position(story_id=story_id)
        self._repository.add_summary_to_story(
            story_id=story_id, summary_id=summary_id, position=position
        )

        # Tag with themes if provided
        if theme_slugs:
            self._apply_theme_slugs(summary_id, theme_slugs)

        return summary_id

    def _apply_theme_slugs(
        self, summary_id: UUID, theme_slugs: list[str]
    ) -> None:
        """Look up theme IDs by slug and create summary_themes associations."""
        for i, slug in enumerate(theme_slugs[:3]):
            theme = self._repository.get_theme_by_slug(slug)
            if theme is None:
                log.warning(f"Unknown theme slug '{slug}' for summary {summary_id}")
                continue
            try:
                self._repository.add_summary_theme(
                    summary_id=summary_id,
                    theme_id=theme.id,
                    is_primary=(i == 0),
                )
            except Exception:
                log.warning(
                    f"Failed to add theme '{slug}' to summary {summary_id} "
                    f"(may already exist)"
                )

    def search_people_by_name(self, name: str) -> list[dict]:
        """Search for people tags by name."""
        return self._repository.search_tags_by_name_and_type(
            name=name, tag_type="PERSON"
        )

    def search_places(
        self,
        name: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float = 1.0,
    ) -> list[dict]:
        """Search for places by name and/or coordinates."""
        return self._repository.search_places_by_name_and_coordinates(
            name=name, latitude=latitude, longitude=longitude, radius=radius
        )

    def find_matching_summary(
        self,
        person_ids: list[UUID],
        place_id: UUID,
        datetime_val: str,
        calendar_model: str,
        precision: int,
    ) -> dict | None:
        """Find an existing summary matching the given tags."""
        return self._repository.find_matching_summary(
            person_ids=person_ids,
            place_id=place_id,
            datetime_val=datetime_val,
            calendar_model=calendar_model,
            precision=precision,
        )

    def create_text_reader_story(
        self,
        name: str,
        description: str | None = None,
        source_id: UUID | None = None,
    ) -> dict:
        """Create a text-reader story."""
        id = uuid4()
        self._repository.create_text_reader_story(
            id=id, name=name, description=description, source_id=source_id
        )
        return {
            "id": id,
            "name": name,
            "description": description,
            "source_id": source_id,
        }

    def get_story_by_source_id(self, source_id: UUID) -> dict | None:
        """Get a text-reader story by source_id."""
        return self._repository.get_story_by_source_id(source_id=source_id)

    def check_time_exists(
        self, datetime: str, calendar_model: str, precision: int
    ) -> UUID | None:
        """Check if a time with the given parameters exists in the database.

        Args:
            datetime: The datetime string to check
            calendar_model: The calendar model to check
            precision: The time precision value to check

        Returns:
            tuple: (exists, id) where exists is True if a matching time exists, False otherwise
                  and id is the UUID of the matching time if exists is True, None otherwise
        """
        with Session(self._repository._engine, future=True) as session:
            return self._repository.time_exists(
                datetime=datetime,
                calendar_model=calendar_model,
                precision=precision,
                session=session,
            )

    def get_themes(self):
        """Return the full theme taxonomy (categories with children)."""
        return self._repository.get_themes()

    # -------------------------------------------------------------------
    # User engagement
    # -------------------------------------------------------------------

    def add_favorite(self, user_id: str, summary_id: UUID) -> None:
        self._repository.add_favorite(user_id=user_id, summary_id=summary_id)

    def remove_favorite(self, user_id: str, summary_id: UUID) -> None:
        self._repository.remove_favorite(user_id=user_id, summary_id=summary_id)

    def get_favorites(self, user_id: str) -> list[dict]:
        return self._repository.get_favorites(user_id=user_id)

    def record_view(self, user_id: str, summary_id: UUID) -> None:
        self._repository.record_view(user_id=user_id, summary_id=summary_id)

    def get_feed(
        self,
        limit: int = 20,
        theme_slugs: list[str] | None = None,
        after_cursor: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """Return a paginated feed with tags and themes."""
        rows = self._repository.get_feed(
            limit=limit,
            theme_slugs=theme_slugs,
            after_cursor=after_cursor,
            user_id=user_id,
        )
        if not rows:
            return {"events": [], "next_cursor": None}

        summary_ids = [r["summary_id"] for r in rows]
        tags_map = self._repository.get_feed_tags(summary_ids)
        themes_map = self._repository.get_feed_themes(summary_ids)

        events = []
        for r in rows:
            sid = r["summary_id"]
            events.append(
                {
                    "summary_id": sid,
                    "summary_text": r["summary_text"],
                    "tags": tags_map.get(sid, []),
                    "themes": themes_map.get(sid, []),
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "datetime": r["datetime"],
                    "precision": r["precision"],
                    "is_favorited": r["is_favorited"],
                }
            )

        # Build cursor from last row
        last = rows[-1]
        next_cursor = (
            f"{last['interleave_rank']}:{last['summary_id']}"
            if len(rows) == limit
            else None
        )
        return {"events": events, "next_cursor": next_cursor}

    # -------------------------------------------------------------------
    # User collections
    # -------------------------------------------------------------------

    def create_collection(
        self, user_id: str, name: str, description: str | None = None
    ) -> dict:
        collection_id = uuid4()
        return self._repository.create_collection(
            id=collection_id, user_id=user_id, name=name, description=description
        )

    def get_collections(self, user_id: str) -> list[dict]:
        return self._repository.get_collections_for_user(user_id=user_id)

    def get_collection(self, collection_id: UUID) -> dict | None:
        return self._repository.get_collection(collection_id=collection_id)

    def update_collection(
        self, collection_id: UUID, **kwargs
    ) -> None:
        self._repository.update_collection(collection_id=collection_id, **kwargs)

    def delete_collection(self, collection_id: UUID) -> None:
        self._repository.delete_collection(collection_id=collection_id)

    def add_collection_item(
        self, collection_id: UUID, summary_id: UUID
    ) -> int:
        item_id = uuid4()
        return self._repository.add_collection_item(
            id=item_id, collection_id=collection_id, summary_id=summary_id
        )

    def remove_collection_item(
        self, collection_id: UUID, summary_id: UUID
    ) -> None:
        self._repository.remove_collection_item(
            collection_id=collection_id, summary_id=summary_id
        )

    def get_collection_items(self, collection_id: UUID) -> list[dict]:
        return self._repository.get_collection_items(collection_id=collection_id)
