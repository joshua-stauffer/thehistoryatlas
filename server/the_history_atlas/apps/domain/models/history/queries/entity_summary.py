from typing import Literal, List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class EntitySummary(ConfiguredBaseModel):
    type: Literal["PERSON", "PLACE", "TIME"]
    id: str
    citation_count: int
    names: List[str]
    first_citation_date: str
    last_citation_date: str
