from typing import Literal
from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class PlaceModel(ConfiguredBaseModel):
    id: UUID
    type: Literal["PLACE"] = "PLACE"
    latitude: float
    longitude: float
    geoshape: str | None = None
    geonames_id: int | None = None
