from dataclasses import dataclass
from typing import Literal, TypedDict


class PersonAddedPayload(TypedDict):
    summary_id: str
    person_id: str
    person_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PersonAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: PersonAddedPayload
    type: Literal["PERSON_ADDED"] = "PERSON_ADDED"
