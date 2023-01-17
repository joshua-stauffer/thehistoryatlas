from dataclasses import dataclass
from typing import Literal, List, Optional

from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.core import Time


@dataclass(frozen=True)
class AddTime:
    user_id: str
    timestamp: str
    app_version: str
    payload: "AddTimePayload"
    type: Literal["ADD_TIME"] = "ADD_TIME"


@dataclass(frozen=True)
class AddTimePayload:
    names: List[AddName]
    time: Time
    desc: Optional[List[AddDescription]] = None
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
