from dataclasses import dataclass
from typing import Literal, TypedDict


@dataclass(frozen=True)
class SummaryTaggedPayload:
    citation_id: str
    summary_id: str


@dataclass(frozen=True)
class SummaryTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: SummaryTaggedPayload
    type: Literal["SUMMARY_TAGGED"] = "SUMMARY_TAGGED"
