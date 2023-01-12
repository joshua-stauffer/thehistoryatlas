from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Time:
    """
    Canonical representation of a time.
    """

    timestamp: str
    precision: Literal[6, 7, 8, 9, 10, 11]  # millennium through day
    calendar_type: Literal["gregorian", "julian"] = "gregorian"
    circa: bool = False
    latest: bool = False
    earliest: bool = False
