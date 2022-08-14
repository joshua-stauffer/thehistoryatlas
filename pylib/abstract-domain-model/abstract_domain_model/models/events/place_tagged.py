from dataclasses import dataclass
from typing import Literal, TypedDict


@dataclass(frozen=True)
class PlaceTaggedPayload:
    summary_id: str
    place_id: str
    place_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PlaceTagged:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: PlaceTaggedPayload
    type: Literal["PLACE_TAGGED"] = "PLACE_TAGGED"
