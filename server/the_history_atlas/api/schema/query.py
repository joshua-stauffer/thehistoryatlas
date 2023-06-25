from ariadne import ObjectType

from the_history_atlas.api.resolvers import resolve_get_user, resolve_is_username_unique


def build_query() -> ObjectType:

    object = ObjectType("Query")
    # object.set_field(
    #     name="GetSummariesByGUID"
    # )
    # object.set_field(
    #     name="GetEntitySummariesByGUID"
    # )
    # object.set_field(
    #     name="GetCitationByGUID"
    # )
    # object.set_field(
    #     name="GetManifest"
    # )
    # object.set_field(
    #     name="GetGUIDsByName"
    # )
    # object.set_field(
    #     name="GetCoordinatesByName"
    # )
    # object.set_field(
    #     name="GetFuzzySearchByName"
    # )
    # object.set_field(
    #     name="GetTextAnalysis"
    # )
    object.set_field(name="IsUsernameUnique", resolver=resolve_is_username_unique)
    object.set_field(name="GetUser", resolver=resolve_get_user)
    # object.set_field(
    #     name="GetPlaceByCoords"
    # )

    return object
