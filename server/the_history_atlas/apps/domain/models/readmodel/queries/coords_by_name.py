from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class Coords(ConfiguredBaseModel):
    latitude: float
    longitude: float


class CoordsByName(ConfiguredBaseModel):
    coords: dict[str, list[Coords]]
