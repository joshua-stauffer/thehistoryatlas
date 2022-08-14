from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PersonTaggedPayload:
    summary_id: str
    citation_id: str
    id: str
    name: str
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
