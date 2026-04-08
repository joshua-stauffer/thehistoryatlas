from datetime import datetime
from uuid import UUID

from the_history_atlas.apps.domain.models.history.tables import TimeModel

TIMES: list[TimeModel] = [
    TimeModel(
        id=UUID("7c4fa5a6-152d-403d-b3d1-5a586578dba4"),
        datetime="+1685-03-21T00:00:00Z",
        calendar_model="http://www.wikidata.org/entity/Q1985727",
        precision=9,
    )
]
