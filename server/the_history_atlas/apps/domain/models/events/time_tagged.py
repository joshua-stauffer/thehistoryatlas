from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class TimeTaggedPayload:
    summary_id: str
    citation_id: str
    id: str
    name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class TimeTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: TimeTaggedPayload
    type: Literal["TIME_TAGGED"] = "TIME_TAGGED"
    index: Optional[int] = None
