import logging
from typing import Dict, List

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.models.readmodel import DefaultEntity, Source
from the_history_atlas.apps.domain.models.readmodel.queries import (
    GetSummariesByID,
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
from the_history_atlas.apps.domain.transform import from_dict
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.event_handler import EventHandler
from the_history_atlas.apps.readmodel.query_handler import QueryHandler

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class ReadModel:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        self._database = Database(engine=database_client)
        self._query_handler = QueryHandler(database_instance=self._database)
        self._event_handler = EventHandler(database_instance=self._database)

    def handle_event(self, event: Dict):
        event = from_dict(event)
        self._event_handler.handle_event(event=event)

    def get_summaries_by_id(self, query: GetSummariesByID) -> List[Summary]:
        return self._query_handler.get_summaries_by_id(query)

    def get_citation_by_id(self, query: GetCitationByID) -> Citation:
        return self._query_handler.get_citation_by_id(query)

    def get_manifest(self, query: GetManifest) -> Manifest:
        return self._query_handler.get_manifest(query)

    def get_entity_summaries_by_name(
        self, query: GetEntitySummariesByName
    ) -> EntitySummariesByName:
        return self._query_handler.get_entity_summaries_by_name(query)

    def get_entity_summaries_by_name_batch(
        self, query: GetEntityIDsByNames
    ) -> EntityIDsByNames:
        return self._query_handler.get_entity_ids_by_names(query)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> List[FuzzySearchByName]:
        return self._query_handler.get_fuzzy_search_by_name(query)

    def get_entity_summaries_by_ids(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        return self._query_handler.get_entity_summaries_by_id(query)

    def get_place_by_coords(self, query: GetPlaceByCoords) -> PlaceByCoords:
        return self._query_handler.get_place_by_coords(query)

    def get_default_entity(self) -> DefaultEntity:
        return self._database.get_default_entity()

    def get_sources_by_search_term(self, search_term: str) -> List[Source]:
        return self._database.get_sources_by_search_term(search_term=search_term)
