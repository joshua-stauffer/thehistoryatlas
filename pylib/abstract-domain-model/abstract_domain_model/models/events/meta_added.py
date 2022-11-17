from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class MetaAddedPayload:
    citation_id: str
    id: str
    title: str
    author: str
    publisher: str
    kwargs: dict


@dataclass(frozen=True)
class MetaAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: MetaAddedPayload
    type: Literal["META_ADDED"] = "META_ADDED"
    index: Optional[int] = None
