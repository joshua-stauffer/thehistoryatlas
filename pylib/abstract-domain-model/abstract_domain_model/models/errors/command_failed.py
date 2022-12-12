from dataclasses import dataclass
from typing import Literal

TYPE = "COMMAND_FAILED"


@dataclass
class CommandFailed:
    type: Literal[TYPE]
    payload: "CommandFailedPayload"


@dataclass
class CommandFailedPayload:
    reason: str
