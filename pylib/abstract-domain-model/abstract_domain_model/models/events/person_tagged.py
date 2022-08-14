from dataclasses import dataclass
from typing import Literal, TypedDict


class PersonTaggedPayload(TypedDict):
    summary_id: str
    person_id: str
    person_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PersonTagged:

    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: PersonTaggedPayload
    type: Literal["PERSON_TAGGED"] = "PERSON_TAGGED"
