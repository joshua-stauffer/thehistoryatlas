from dataclasses import dataclass
from typing import Literal, Optional, List

from abstract_domain_model.models.core.description import Description
from abstract_domain_model.models.core.name import Name
from abstract_domain_model.models.core.geo import Geo


@dataclass(frozen=True)
class PlaceAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: "PlaceAddedPayload"
    type: Literal["PLACE_ADDED"] = "PLACE_ADDED"
    index: Optional[int] = None


@dataclass(frozen=True)
class PlaceAddedPayload:
    id: str
    names: List[Name]
    geo: Geo
    desc: Optional[List[Description]] = None
    wiki_link: Optional[str] = None
    wiki_data_id: Optional[str] = None
    geo_names_id: Optional[str] = None
