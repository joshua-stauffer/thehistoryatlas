from dataclasses import dataclass
from typing import Literal, TypedDict


class PersonTaggedPayload(TypedDict):
    summary_guid: str
    person_guid: str
    person_name: str
    citation_start: int
    citation_end: int


@dataclass(frozen=True)
class PersonTagged:

    transaction_guid: str
    app_version: str
    timestamp: str
    user: str
    payload: PersonTaggedPayload
    type: Literal["PERSON_TAGGED"] = "PERSON_TAGGED"
