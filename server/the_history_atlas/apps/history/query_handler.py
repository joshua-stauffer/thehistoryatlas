import logging
from typing import List, Literal
from uuid import UUID

from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.core import (
    TagPointer,
    Story,
    StoryPointer,
    HistoryEvent,
    CalendarDate,
    Source as CoreSource,
    Map,
    Point,
    Tag,
)

from the_history_atlas.apps.domain.models.history.get_fuzzy_search_by_name import (
    GetFuzzySearchByName,
    FuzzySearchByName,
)
from the_history_atlas.apps.history.errors import (
    MissingResourceError,
)
from the_history_atlas.apps.history.database import Database
from the_history_atlas.apps.history.trie import Trie

log = logging.getLogger(__name__)


class QueryHandler:
    def __init__(
        self, database_instance: Database, source_trie: Trie, entity_trie: Trie
    ):
        self._db = database_instance
        self._source_trie = source_trie
        self._entity_trie = entity_trie

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> List[FuzzySearchByName]:
        """Perform a fuzzy search on the given string and return possible completions."""
        fuzzy_search_by_name_collection = self._db.get_name_by_fuzzy_search(query.name)
        return fuzzy_search_by_name_collection

    def get_tags_by_wikidata_ids(self, wikidata_ids: list[str]) -> list[TagPointer]:
        return self._db.get_tags_by_wikidata_ids(wikidata_ids=wikidata_ids)

    def get_story_list(
        self, event_id: UUID, story_id: UUID, direction: Literal["next", "prev"] | None
    ) -> Story:
        with self._db.Session() as session:
            story_pointers = self.get_story_pointers(
                event_id=event_id,
                story_id=story_id,
                direction=direction,
                session=session,
            )
            events = self._db.get_events(
                event_ids=tuple([story.event_id for story in story_pointers]),
                session=session,
            )
            story_names = self._db.get_story_names(
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
                    time=event_query.calendar_date.datetime,
                    calendar=event_query.calendar_date.calendar_model,
                    precision=event_query.calendar_date.precision,
                ),
                source=CoreSource(
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
        story_pointers = self._db.get_story_pointers(
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
            related_story = self._db.get_related_story(
                summary_id=last_story_pointer.event_id,
                tag_id=last_story_pointer.story_id,
                direction=DIRECTION,
                session=session,
            )
            if not related_story:
                break
            related_story_pointers = self._db.get_story_pointers(
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
        story_pointers = self._db.get_story_pointers(
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
            related_story = self._db.get_related_story(
                summary_id=last_story_pointer.event_id,
                tag_id=last_story_pointer.story_id,
                direction=DIRECTION,
                session=session,
            )
            if not related_story:
                break
            related_story_pointers = self._db.get_story_pointers(
                summary_id=related_story.event_id,
                tag_id=related_story.story_id,
                direction=DIRECTION,
                session=session,
            )
            story_pointers = [*related_story_pointers, related_story, *story_pointers]
        return story_pointers

    def get_default_story_and_event(
        self,
        story_id: UUID | None,
        event_id: UUID | None,
    ) -> StoryPointer:
        if story_id:
            # get the first story
            return self._db.get_default_event_by_story(story_id=story_id)
        elif event_id:
            # get the person story associated with this event
            return self._db.get_default_story_by_event(event_id=event_id)
        else:
            # return random story/event
            return self._db.get_default_story_and_event()
