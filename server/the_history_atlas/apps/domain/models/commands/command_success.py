from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class CommandSuccess(ConfiguredBaseModel):
    type: Literal["COMMAND_SUCCESS"] = "COMMAND_SUCCESS"
    token: str
