from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PersonAddedPayload:
    summary_id: str
    id: str
    name: str
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
