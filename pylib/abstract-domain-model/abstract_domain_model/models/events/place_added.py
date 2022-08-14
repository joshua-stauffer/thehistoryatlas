from dataclasses import dataclass
from typing import Literal, TypedDict, Optional


@dataclass(frozen=True)
class PlaceAddedPayload:
    summary_id: str
    place_id: str
    place_name: str
    citation_start: int
    citation_end: int
    longitude: float
    latitude: float
    geoshape: Optional[str]


@dataclass(frozen=True)
class PlaceAdded:

    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: PlaceAddedPayload
    type: Literal["PLACE_ADDED"] = "PLACE_ADDED"
