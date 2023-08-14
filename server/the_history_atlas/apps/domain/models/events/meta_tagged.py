from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class MetaTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: "MetaTaggedPayload"
    type: Literal["META_TAGGED"] = "META_TAGGED"
    index: Optional[int] = None


@dataclass(frozen=True)
class MetaTaggedPayload:
    citation_id: str
    id: str
