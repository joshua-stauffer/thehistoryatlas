import logging
from typing import Dict, List

from the_history_atlas.apps.database import DatabaseClient
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
    EntitySummariesByNameBatchResult,
    GetFuzzySearchByName,
    FuzzySearchByName,
    GetEntitySummariesByIDs,
    GetPlaceByCoords,
    GetPlaceByCoordsResult,
)
from the_history_atlas.apps.domain.transform import from_dict
from the_history_atlas.apps.readmodel.api.api import GQLApi
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.readmodel.state_manager.database import Database
from the_history_atlas.apps.readmodel.state_manager.event_handler import EventHandler
from the_history_atlas.apps.readmodel.state_manager.query_handler import QueryHandler

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class ReadModel:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        self._database = Database(engine=database_client)
        self._query_handler = QueryHandler(database_instance=self._database)
        self._event_handler = EventHandler(database_instance=self._database)

        self.api = GQLApi(
            default_entity_handler=self.manager.db.get_default_entity,
            search_sources_handler=self.manager.db.get_sources_by_search_term,
        )

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
    ) -> List[EntitySummary]:
        return self._query_handler.get_entity_summaries_by_name(query)

    def get_entity_summaries_by_name_batch(
        self, query: GetEntityIDsByNames
    ) -> EntitySummariesByNameBatchResult:
        return self._query_handler.get_entity_ids_by_names(query)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> FuzzySearchByName:
        return self._query_handler.get_fuzzy_search_by_name(query)

    def get_entity_summaries_by_ids(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        return self._query_handler.get_entity_summaries_by_id(query)

    def get_place_by_coords(self, query: GetPlaceByCoords) -> GetPlaceByCoordsResult:
        return self._query_handler.get_place_by_coords(query)
