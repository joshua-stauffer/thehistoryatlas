from dataclasses import dataclass
from typing import Literal, TypedDict, List


class CitationAddedPayload(TypedDict):
    summary_id: str
    citation_id: str
    text: str
    tags: List[str]
    meta: str


@dataclass(frozen=True)
class CitationAdded:

    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: CitationAddedPayload
    type: Literal["CITATION_ADDED"] = "CITATION_ADDED"
