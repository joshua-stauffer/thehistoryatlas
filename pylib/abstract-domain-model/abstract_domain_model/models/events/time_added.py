from dataclasses import dataclass
from typing import Literal, TypedDict


@dataclass(frozen=True)
class TimeAddedPayload:
    summary_id: str
    id: str
    name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class TimeAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: TimeAddedPayload
    type: Literal["TIME_ADDED"] = "TIME_ADDED"
