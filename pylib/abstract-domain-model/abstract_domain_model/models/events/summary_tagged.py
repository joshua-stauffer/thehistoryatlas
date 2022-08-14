from dataclasses import dataclass
from typing import Literal, TypedDict


class SummaryTaggedPayload(TypedDict):
    citation_id: str
    summary_id: str


@dataclass(frozen=True)
class SummaryTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user: str
    payload: SummaryTaggedPayload
    type: Literal["SUMMARY_TAGGED"] = "SUMMARY_TAGGED"
