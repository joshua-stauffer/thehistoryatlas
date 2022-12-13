from dataclasses import dataclass
from typing import Literal

TYPE = "COMMAND_FAILED"


@dataclass
class CommandFailed:
    payload: "CommandFailedPayload"
    type: Literal[TYPE] = TYPE


@dataclass
class CommandFailedPayload:
    reason: str
