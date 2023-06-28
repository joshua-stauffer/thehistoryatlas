import logging
from typing import List

from the_history_atlas.apps.domain.models.readmodel.queries import (
    GetCitationByID,
    Citation,
    GetSummariesByID,
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
    GetPlaceByCoordsResult,
    EntitySummariesByNameResult,
    EntityIDsByNamesResult,
)
from the_history_atlas.apps.readmodel.errors import (
    UnknownManifestTypeError,
)
from the_history_atlas.apps.readmodel.state_manager.database import Database

log = logging.getLogger(__name__)


class QueryHandler:
    def __init__(self, database_instance: Database):
        self._db = database_instance

    def get_summaries_by_id(self, query: GetSummariesByID) -> List[Summary]:
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
    ) -> EntitySummariesByNameResult:
        """Fetch a list of guids associated with a given name"""
        name_ids = self._db.get_guids_by_name(query.name)
        entity_summaries = self._db.get_entity_summary_by_guid_batch(name_ids)
        return EntitySummariesByNameResult.parse_obj(
            {"ids": name_ids, "summaries": entity_summaries}
        )

    def get_entity_ids_by_names(
        self, query: GetEntityIDsByNames
    ) -> EntityIDsByNamesResult:
        """Fetch GUIDs for a series of names. Used internally by other services."""
        name_ids_map: dict[str, list[str]] = dict()
        for name in query.names:
            ids = self._db.get_guids_by_name(name)
            name_ids_map[name] = ids
        return EntityIDsByNamesResult(names=name_ids_map)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> FuzzySearchByName:
        """Perform a fuzzy search on the given string and return possible completions."""
        results = self._db.get_name_by_fuzzy_search(query.name)
        return FuzzySearchByName.parse_obj({"name": query.name, "results": results})

    def get_entity_summaries_by_id(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        """Resolve a list of entity GUIDs into summaries"""
        entity_summaries = self._db.get_entity_summary_by_guid_batch(query.ids)
        return [
            EntitySummary.parse_obj(entity_summary)
            for entity_summary in entity_summaries
        ]

    def get_place_by_coords(self, query: GetPlaceByCoords) -> GetPlaceByCoordsResult:
        """Resolve a place, if any, from a set of latitude and longitude"""
        id = self._db.get_place_by_coords(
            latitude=query.latitude, longitude=query.longitude
        )
        return GetPlaceByCoordsResult(
            latitude=query.latitude, longitude=query.longitude, id=id
        )
