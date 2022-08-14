from dataclasses import dataclass
from typing import Literal, TypedDict, Optional


class PlaceAddedPayload(TypedDict):
    summary_guid: str
    place_guid: str
    place_name: str
    citation_start: int
    citation_end: int
    longitude: float
    latitude: float
    geoshape: Optional[str]


@dataclass(frozen=True)
class PlaceAdded:

    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: PlaceAddedPayload
    type: Literal["PLACE_ADDED"] = "PLACE_ADDED"
