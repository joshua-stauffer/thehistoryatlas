from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Name:
    """
    Canonical Name Event.
    """

    id: str
    name: str
    lang: str
    is_default: bool
    is_historic: bool = False
    start_time: Optional[str] = None
    end_time: Optional[str] = None
