from dataclasses import dataclass
from typing import Literal, TypedDict


class MetaAddedPayload(TypedDict):
    citation_id: str
    meta_id: str
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
