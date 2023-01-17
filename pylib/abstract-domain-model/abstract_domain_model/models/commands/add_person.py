from dataclasses import dataclass
from typing import Literal, List, Optional

from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.models.commands.description import AddDescription


@dataclass(frozen=True)
class AddPerson:
    user_id: str
    timestamp: str
    app_version: str
    payload: "AddPersonPayload"
    type: Literal["ADD_PERSON"] = "ADD_PERSON"


@dataclass(frozen=True)
class AddPersonPayload:
    names: List[AddName]
    desc: Optional[List[AddDescription]] = None
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
