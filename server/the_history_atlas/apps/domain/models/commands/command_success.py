from dataclasses import dataclass
from typing import Literal

TYPE = "COMMAND_SUCCESS"


@dataclass
class CommandSuccess:
    type: Literal[TYPE] = TYPE
