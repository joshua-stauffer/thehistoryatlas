import logging
from typing import List

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.core import PersonInput, Person
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.readmodel import DefaultEntity, Source
from the_history_atlas.apps.domain.models.readmodel.queries import (
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
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.event_handler import EventHandler
from the_history_atlas.apps.readmodel.query_handler import QueryHandler
from the_history_atlas.apps.readmodel.trie import Trie

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class ReadModelApp:
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

    def handle_event(self, event: Event):
        self._event_handler.handle_event(event=event)

    def get_summaries_by_ids(self, query: GetSummariesByIDs) -> List[Summary]:
        return self._query_handler.get_summaries_by_id(query)

    def get_citation_by_id(self, query: GetCitationByID) -> Citation:
        return self._query_handler.get_citation_by_id(query)

    def get_manifest(self, query: GetManifest) -> Manifest:
        return self._query_handler.get_manifest(query)

    def get_entity_summaries_by_name(
        self, query: GetEntitySummariesByName
    ) -> EntitySummariesByName:
        return self._query_handler.get_entity_summaries_by_name(query)

    def get_entity_ids_by_names(self, query: GetEntityIDsByNames) -> EntityIDsByNames:
        return self._query_handler.get_entity_ids_by_names(query)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> List[FuzzySearchByName]:
        return self._query_handler.get_fuzzy_search_by_name(query)

    def get_entity_summaries_by_ids(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        return self._query_handler.get_entity_summaries_by_ids(query)

    def get_place_by_coords(self, query: GetPlaceByCoords) -> PlaceByCoords:
        return self._query_handler.get_place_by_coords(query)

    def get_default_entity(self) -> DefaultEntity:
        return self._query_handler.get_default_entity()

    def get_sources_by_search_term(self, search_term: str) -> List[Source]:
        return self._query_handler.get_sources_by_search_term(search_term=search_term)

    def get_coords_by_names(self, names: list[str]) -> CoordsByName:
        return self._query_handler.get_coords_by_names(names=names)

    def create_person(self, person: PersonInput) -> Person:
        ...
