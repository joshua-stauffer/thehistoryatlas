from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel

TYPE = "COMMAND_FAILED"


class CommandFailedPayload(ConfiguredBaseModel):
    reason: str


class CommandFailed(ConfiguredBaseModel):
    payload: "CommandFailedPayload"
    type: Literal[TYPE] = TYPE
    token: str
