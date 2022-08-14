from dataclasses import dataclass
from typing import Literal, TypedDict


class SummaryTaggedPayload(TypedDict):
    citation_guid: str
    summary_guid: str


@dataclass(frozen=True)
class SummaryTagged:
    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: SummaryTaggedPayload
    type: Literal["SUMMARY_TAGGED"] = "SUMMARY_TAGGED"
