import logging
from typing import List

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
