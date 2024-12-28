from dataclasses import dataclass
from typing import Literal

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel



class CommandFailedPayload(ConfiguredBaseModel):
    reason: str


class CommandFailed(ConfiguredBaseModel):
    payload: "CommandFailedPayload"
    type: Literal[ "COMMAND_FAILED"] =  "COMMAND_FAILED"
    token: str
