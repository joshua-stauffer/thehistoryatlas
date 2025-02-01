from typing import List
from uuid import UUID

from the_history_atlas.apps.domain.models.history.tables import PlaceModel

PLACES: List[PlaceModel] = [
    PlaceModel(
        id=UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86"),
        latitude=10.3147,
        longitude=50.9796,
        geoshape=None,
        geonames_id=None,
    )
]
