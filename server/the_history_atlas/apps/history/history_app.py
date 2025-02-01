import logging
from typing import List, Literal
from uuid import UUID

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
)
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.history import DefaultEntity, Source
from the_history_atlas.apps.domain.models.history.queries import (
    GetSummariesByIDs,
    Summary,
    GetCitationByID,
    Citation,
    GetManifest,
    Manifest,
    GetEntitySummariesByName,
    EntitySummary,
    GetEntityIDsByNames,
    EntityIDsByNames,
    GetFuzzySearchByName,
    FuzzySearchByName,
    GetEntitySummariesByIDs,
    GetPlaceByCoords,
    PlaceByCoords,
    EntitySummariesByName,
)
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.history.database import Database
from the_history_atlas.apps.history.event_handler import EventHandler
from the_history_atlas.apps.history.query_handler import QueryHandler
from the_history_atlas.apps.history.trie import Trie

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class HistoryApp:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        source_trie = Trie()
        entity_trie = Trie()

        database = Database(
            database_client=database_client,
            source_trie=source_trie,
            entity_trie=entity_trie,
        )
        source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
        entity_trie.build(entity_tuples=database.get_all_entity_names())
        self._query_handler = QueryHandler(
            database_instance=database, source_trie=source_trie, entity_trie=entity_trie
        )
        self._event_handler = EventHandler(
            database_instance=database, source_trie=source_trie, entity_trie=entity_trie
        )

    def get_sources_by_search_term(self, search_term: str) -> List[Source]:
        return self._query_handler.get_sources_by_search_term(search_term=search_term)

    def create_person(self, person: PersonInput) -> Person:
        return self._event_handler.create_person(person=person)

    def create_place(self, place: PlaceInput) -> Place:
        return self._event_handler.create_place(place=place)

    def create_time(self, time: TimeInput) -> Time:
        return self._event_handler.create_time(time=time)

    def get_tags_by_wikidata_ids(self, ids: list[str]) -> list[TagPointer]:
        return self._query_handler.get_tags_by_wikidata_ids(wikidata_ids=ids)

    def create_wikidata_event(
        self,
        text: str,
        tags: list[TagInstance],
        citation: CitationInput,
    ):
        return self._event_handler.create_wikidata_event(
            text=text, tags=tags, citation=citation
        )

    def get_story_list(
        self, event_id: UUID, story_id: UUID, direction: Literal["next", "prev"] | None
    ) -> Story:
        return self._query_handler.get_story_list(
            event_id=event_id, story_id=story_id, direction=direction
        )

    def get_default_story_and_event(
        self,
        story_id: UUID | None,
        event_id: UUID | None,
    ) -> StoryPointer:
        return self._query_handler.get_default_story_and_event(
            story_id=story_id, event_id=event_id
        )
