from typing import Any

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class CoordsByName(ConfiguredBaseModel):
    coords: Any
