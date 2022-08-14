from dataclasses import dataclass
from typing import Literal, TypedDict


class MetaAddedPayload(TypedDict):
    citation_guid: str
    meta_guid: str
    title: str
    author: str
    publisher: int
    kwargs: dict


@dataclass(frozen=True)
class MetaAdded:
    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: MetaAddedPayload
    type: Literal["META_ADDED"] = "META_ADDED"
