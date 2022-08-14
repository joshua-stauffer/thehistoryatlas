from dataclasses import dataclass
from typing import Literal, TypedDict


class PlaceTaggedPayload(TypedDict):
    summary_guid: str
    place_guid: str
    place_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PlaceTagged:
    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: PlaceTaggedPayload
    type: Literal["PLACE_TAGGED"] = "PLACE_TAGGED"
