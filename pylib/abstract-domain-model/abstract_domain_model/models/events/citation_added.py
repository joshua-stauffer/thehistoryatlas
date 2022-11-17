from dataclasses import dataclass
from typing import Literal, List, Optional


@dataclass(frozen=True)
class CitationAddedPayload:
    id: str
    text: str
    summary_id: str
    meta_id: str


@dataclass(frozen=True)
class CitationAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: CitationAddedPayload
    type: Literal["CITATION_ADDED"] = "CITATION_ADDED"
    index: Optional[int] = None
