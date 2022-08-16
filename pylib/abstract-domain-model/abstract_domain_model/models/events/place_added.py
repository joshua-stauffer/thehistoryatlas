from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class PlaceAddedPayload:
    summary_id: str
    citation_id: str
    id: str
    name: str
    citation_start: int
    citation_end: int
    longitude: float
    latitude: float
    geo_shape: Optional[str]


@dataclass(frozen=True)
class PlaceAdded:

    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: PlaceAddedPayload
    type: Literal["PLACE_ADDED"] = "PLACE_ADDED"
