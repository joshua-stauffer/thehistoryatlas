from dataclasses import dataclass
from typing import Literal, Optional, List

from abstract_domain_model.models.core.description import Description
from abstract_domain_model.models.core.name import Name


@dataclass(frozen=True)
class PersonAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: "PersonAddedPayload"
    type: Literal["PERSON_ADDED"] = "PERSON_ADDED"
    index: Optional[int] = None


@dataclass(frozen=True)
class PersonAddedPayload:
    id: str
    names: List[Name]
    desc: Optional[Description]
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
