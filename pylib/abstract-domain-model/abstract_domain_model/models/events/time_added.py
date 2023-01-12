from dataclasses import dataclass
from typing import Literal, Optional, List

from abstract_domain_model.models.events.description import Description
from abstract_domain_model.models.events.name import Name
from abstract_domain_model.models.events.time import Time


@dataclass(frozen=True)
class TimeAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: "TimeAddedPayload"
    type: Literal["TIME_ADDED"] = "TIME_ADDED"
    index: Optional[int] = None


@dataclass(frozen=True)
class TimeAddedPayload:
    id: str
    names: List[Name]
    time: Time
    desc: Optional[Description] = None
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
