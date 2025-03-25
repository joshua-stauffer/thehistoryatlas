import logging
from typing import Literal
from uuid import UUID, uuid4

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
from the_history_atlas.apps.history.repository import Repository
from the_history_atlas.apps.history.errors import TagExistsError, MissingResourceError
from the_history_atlas.apps.history.trie import Trie

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class HistoryApp:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        source_trie = Trie()
        entity_trie = Trie()

        repository = Repository(
            database_client=database_client,
            source_trie=source_trie,
            entity_trie=entity_trie,
        )
        self._repository = repository
        self._source_trie = source_trie.build(
            entity_tuples=repository.get_all_source_titles_and_authors()
        )
        self._entity_trie = entity_trie.build(
            entity_tuples=repository.get_all_entity_names()
        )

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
                story_names=self.get_available_person_story_names(name=person.name),
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
                story_names=self.get_available_place_story_names(name=place.name),
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
                story_names=self.get_available_time_story_names(name=time.name),
            )
            session.commit()
        return Time(id=id, **time.model_dump())

    def get_tags_by_wikidata_ids(self, ids: list[str]) -> list[TagPointer]:
        return self._repository.get_tags_by_wikidata_ids(wikidata_ids=ids)

    def fuzzy_search_stories(self, search_string: str) -> list[dict[str, str]]:
        """
        Search for stories that match the given search string.
        Returns a list of dictionaries containing story IDs and names.
        """
        # Get matching IDs from fuzzy search
        matches = self._repository.get_name_by_fuzzy_search(search_string)
        if not matches:
            return []

        # Extract all unique IDs from the matches
        all_ids = set()
        for match in matches:
            all_ids.update(match.ids)

        # Convert set to tuple for SQL query
        story_ids = tuple(all_ids)

        # Get story names for the matching IDs
        with self._repository.Session() as session:
            story_names = self._repository.get_story_names(story_ids, session)

        # Format results as list of dicts
        return [
            {"id": str(story_id), "name": name}
            for story_id, name in story_names.items()
        ]

    def create_wikidata_event(
        self,
        text: str,
        tags: list[TagInstance],
        citation: CitationInput,
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
            self._repository.create_summary(
                id=summary_id,
                text=text,
            )
            citation_text = f"Wikidata. ({citation.access_date}). {citation.wikidata_item_title} ({citation.wikidata_item_id}). Wikimedia Foundation. {citation.wikidata_item_url}"
            citation_id = uuid4()
            self._repository.create_citation(
                id=citation_id,
                session=session,
                citation_text=citation_text,
                access_date=str(citation.access_date),
            )
            self._repository.create_citation_source_fkey(
                session=session,
                citation_id=citation_id,
                source_id=source_id,
            )
            self._repository.create_citation_summary_fkey(
                session=session,
                citation_id=citation_id,
                summary_id=summary_id,
            )
            (
                tag_instance_time,
                precision,
            ) = self._repository.get_time_and_precision_by_tags(
                session=session,
                tag_ids=[tag.id for tag in tags],
            )
            for tag in tags:
                self._repository.create_tag_instance(
                    start_char=tag.start_char,
                    stop_char=tag.stop_char,
                    summary_id=summary_id,
                    tag_id=tag.id,
                    tag_instance_time=tag_instance_time,
                    time_precision=precision,
                    session=session,
                )
            session.commit()
        return summary_id

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
            story_pointer.event_id: story_names[story_pointer.story_id]
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
                story_title=story_names_by_event_id[event_query.event_id],
                stories=list(),  # todo
            )
            for event_query in events
        ]
        return Story(
            id=story_id,
            events=history_events,
            name=story_names[story_id],
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

    def get_available_person_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"The Life of {name}"),
        ]

    def get_available_place_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"The History of {name}"),
        ]

    def get_available_time_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"Events of {name}"),
        ]

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
