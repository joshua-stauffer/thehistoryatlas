from dataclasses import dataclass
from typing import Literal, TypedDict, List


class CitationAddedPayload(TypedDict):
    summary_guid: str
    citation_guid: str
    text: str
    tags: List[str]
    meta: str


@dataclass(frozen=True)
class CitationAdded:

    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: CitationAddedPayload
    type: Literal["CITATION_ADDED"] = "CITATION_ADDED"
