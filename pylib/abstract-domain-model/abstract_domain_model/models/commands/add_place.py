from dataclasses import dataclass
from typing import Literal, List, Optional

from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.core import Geo


@dataclass(frozen=True)
class AddPlace:
    user_id: str
    timestamp: str
    app_version: str
    payload: "AddPlacePayload"
    type: Literal["ADD_PLACE"] = "ADD_PLACE"


@dataclass(frozen=True)
class AddPlacePayload:
    names: List[AddName]
    geo: Geo
    desc: Optional[List[AddDescription]] = None
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
    geo_names_id: Optional[str] = None
