from dataclasses import dataclass
from typing import Literal, TypedDict


class SummaryAddedPayload(TypedDict):
    citation_id: str
    summary_id: str
    text: str


@dataclass(frozen=True)
class SummaryAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user: str
    payload: SummaryAddedPayload
    type: Literal["SUMMARY_ADDED"] = "SUMMARY_ADDED"
