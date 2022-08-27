from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class SummaryTaggedPayload:
    citation_id: str
    id: str


@dataclass(frozen=True)
class SummaryTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: SummaryTaggedPayload
    type: Literal["SUMMARY_TAGGED"] = "SUMMARY_TAGGED"
    index: Optional[int] = None
