from dataclasses import dataclass
from typing import Literal, TypedDict


class TimeTaggedPayload(TypedDict):
    summary_id: str
    time_id: str
    time_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class TimeTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user: str
    payload: TimeTaggedPayload
    type: Literal["TIME_TAGGED"] = "TIME_TAGGED"
