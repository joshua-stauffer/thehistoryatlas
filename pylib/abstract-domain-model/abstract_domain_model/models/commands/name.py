from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AddName:
    """
    Canonical Name Command.
    """

    name: str
    lang: str
    is_default: bool
    is_historic: bool = False
    start_time: Optional[str] = None
    end_time: Optional[str] = None
