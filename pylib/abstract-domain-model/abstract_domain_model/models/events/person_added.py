from dataclasses import dataclass
from typing import Literal, TypedDict


class PersonAddedPayload(TypedDict):
    summary_guid: str
    person_guid: str
    person_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PersonAdded:
    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: PersonAddedPayload
    type: Literal["PERSON_ADDED"] = "PERSON_ADDED"
