from datetime import datetime
from typing import Literal, Union
from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel

TimePrecision = 6 | 7 | 8 | 9 | 10 | 11


class TimeModel(ConfiguredBaseModel):
    id: UUID
    type: Literal["TIME"] = "TIME"
    time: datetime
    calendar_model: str
    precision: Literal[6, 7, 8, 9, 10, 11] = TimePrecision
