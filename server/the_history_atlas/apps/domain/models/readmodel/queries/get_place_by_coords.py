from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetPlaceByCoords(ConfiguredBaseModel):
    latitude: float
    longitude: float


class PlaceByCoords(ConfiguredBaseModel):
    id: str | None
    latitude: float
    longitude: float
