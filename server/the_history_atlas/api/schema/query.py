from ariadne import ObjectType

from the_history_atlas.api.resolvers import (
    resolve_get_user,
    resolve_is_username_unique,
    resolve_get_summaries_by_ids,
    resolve_get_entity_summaries_by_ids,
    resolve_get_citation_by_id,
    resolve_get_manifest,
    resolve_get_entity_summaries_by_name,
    resolve_get_fuzzy_search_by_name,
    resolve_default_entity,
    resolve_search_sources,
)


def build_query() -> ObjectType:

    query = ObjectType("Query")
    query.set_field(name="GetSummariesByGUID", resolver=resolve_get_summaries_by_ids)
    query.set_field(
        name="GetEntitySummariesByGUID", resolver=resolve_get_entity_summaries_by_ids
    )
    query.set_field(name="GetCitationByGUID", resolver=resolve_get_citation_by_id)
    query.set_field(name="GetManifest", resolver=resolve_get_manifest)
    query.set_field(
        name="GetGUIDsByName", resolver=resolve_get_entity_summaries_by_name
    )
    # query.set_field(
    #     name="GetCoordinatesByName"
    # )
    query.set_field(
        name="GetFuzzySearchByName", resolver=resolve_get_fuzzy_search_by_name
    )
    # query.set_field(
    #     name="GetTextAnalysis"
    # )
    query.set_field(name="IsUsernameUnique", resolver=resolve_is_username_unique)
    query.set_field(name="GetUser", resolver=resolve_get_user)
    # query.set_field(
    #     name="GetPlaceByCoords"
    # )
    query.set_field(name="defaultEntity", resolver=resolve_default_entity)
    query.set_field(name="searchSources", resolver=resolve_search_sources)

    return query
