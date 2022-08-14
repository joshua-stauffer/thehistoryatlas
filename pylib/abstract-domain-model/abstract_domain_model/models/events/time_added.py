from dataclasses import dataclass
from typing import Literal, TypedDict


class TimeAddedPayload(TypedDict):
    summary_id: str
    time_id: str
    time_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class TimeAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user: str
    payload: TimeAddedPayload
    type: Literal["TIME_ADDED"] = "TIME_ADDED"
