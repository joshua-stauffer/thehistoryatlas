from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import PlaceByCoords


def resolve_get_place_by_coords(
    _: None, info: Info, latitude: float, longitude: float
) -> PlaceByCoords:
    ...
