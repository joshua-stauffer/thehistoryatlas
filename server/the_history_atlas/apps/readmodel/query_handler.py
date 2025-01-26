import logging
from typing import List, Literal
from uuid import UUID

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
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.readmodel import Source, DefaultEntity
from the_history_atlas.apps.domain.models.readmodel.queries import (
    GetCitationByID,
    Citation,
    GetSummariesByIDs,
    Summary,
    GetManifest,
    Manifest,
    Timeline,
    GetEntitySummariesByName,
    EntitySummary,
    GetEntityIDsByNames,
    GetFuzzySearchByName,
    FuzzySearchByName,
    GetEntitySummariesByIDs,
    GetPlaceByCoords,
    PlaceByCoords,
    EntitySummariesByName,
    EntityIDsByNames,
)
from the_history_atlas.apps.readmodel.errors import (
    UnknownManifestTypeError,
    MissingResourceError,
)
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.trie import Trie

log = logging.getLogger(__name__)


class QueryHandler:
    def __init__(
        self, database_instance: Database, source_trie: Trie, entity_trie: Trie
    ):
        self._db = database_instance
        self._source_trie = source_trie
        self._entity_trie = entity_trie

    def get_summaries_by_id(self, query: GetSummariesByIDs) -> List[Summary]:
        """Fetch a series of summaries by a list of guids"""
        summaries = self._db.get_summaries(summary_guids=query.summary_ids)
        return [Summary.parse_obj(summary) for summary in summaries]

    def get_citation_by_id(self, query: GetCitationByID) -> Citation:
        """Fetch a citation and its associated data by guid"""
        citation_dict = self._db.get_citation(query.citation_id)
        citation = Citation.parse_obj(
            citation_dict
        )  # todo: will error if result not found
        return citation

    def get_manifest(self, query: GetManifest) -> Manifest:
        """Fetch a list of citation guids for a given focus"""
        if query.entity_type == "TIME":
            citation_ids, years = self._db.get_manifest_by_time(query.id)
        elif query.entity_type == "PLACE":
            citation_ids, years = self._db.get_manifest_by_place(query.id)
        elif query.entity_type == "PERSON":
            citation_ids, years = self._db.get_manifest_by_person(query.id)
        else:
            raise UnknownManifestTypeError(query.entity_type)
        return Manifest(
            id=query.id,
            citation_ids=citation_ids,
            timeline=[Timeline.parse_obj(year) for year in years],
        )

    def get_entity_summaries_by_name(
        self, query: GetEntitySummariesByName
    ) -> EntitySummariesByName:
        """Fetch a list of guids associated with a given name"""
        name_ids = self._db.get_guids_by_name(query.name)
        entity_summaries = self._db.get_entity_summary_by_guid_batch(name_ids)
        return EntitySummariesByName.parse_obj(
            {"ids": name_ids, "summaries": entity_summaries}
        )

    def get_entity_ids_by_names(self, query: GetEntityIDsByNames) -> EntityIDsByNames:
        """Fetch GUIDs for a series of names. Used internally by other services."""
        name_ids_map: dict[str, list[str]] = dict()
        for name in query.names:
            ids = self._db.get_guids_by_name(name)
            name_ids_map[name] = ids
        return EntityIDsByNames(names=name_ids_map)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> List[FuzzySearchByName]:
        """Perform a fuzzy search on the given string and return possible completions."""
        fuzzy_search_by_name_collection = self._db.get_name_by_fuzzy_search(query.name)
        return fuzzy_search_by_name_collection

    def get_entity_summaries_by_ids(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        """Resolve a list of entity GUIDs into summaries"""
        entity_summaries = self._db.get_entity_summary_by_guid_batch(query.ids)
        return [
            EntitySummary.parse_obj(entity_summary)
            for entity_summary in entity_summaries
        ]

    def get_place_by_coords(self, query: GetPlaceByCoords) -> PlaceByCoords:
        """Resolve a place, if any, from a set of latitude and longitude"""
        id = self._db.get_place_by_coords(
            latitude=query.latitude, longitude=query.longitude
        )
        return PlaceByCoords(latitude=query.latitude, longitude=query.longitude, id=id)

    def get_sources_by_search_term(self, search_term: str) -> list[Source]:
        if search_term == "":
            return []
        sources = self._source_trie.find(search_term, res_count=10)
        return self._db.get_sources_by_search_term(sources=sources)

    def get_default_entity(self) -> DefaultEntity:
        return self._db.get_default_entity()

    def get_coords_by_names(self, names: list[str]) -> CoordsByName:
        with self._db.Session() as session:
            return self._db.get_coords_by_names(names=names, session=session)

    def get_tags_by_wikidata_ids(self, wikidata_ids: list[str]) -> list[TagPointer]:
        return self._db.get_tags_by_wikidata_ids(wikidata_ids=wikidata_ids)

    def get_story_list(
        self, event_id: UUID, story_id: UUID, direction: Literal["next", "prev"] | None
    ) -> Story:
        with self._db.Session() as session:
            try:
                story_pointers = self._db.get_story_pointers(
                    summary_id=event_id,
                    tag_id=story_id,
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
                            *[
                                story_pointer.story_id
                                for story_pointer in story_pointers
                            ],
                            story_id,
                        }
                    ),
                    session=session,
                )
            except Exception as e:
                raise
        if not story_names:
            raise MissingResourceError("Story not found")

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
                story_title=story_names[story_id],
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
            return self._db.get_default_event_by_story(story_id=story_id)
        elif event_id:
            # get the person story associated with this event
            return self._db.get_default_story_by_event(event_id=event_id)
        else:
            # return random story/event
            return self._db.get_default_story_and_event()
