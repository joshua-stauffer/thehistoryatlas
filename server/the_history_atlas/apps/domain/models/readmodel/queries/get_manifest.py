from typing import Literal, List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetManifest(ConfiguredBaseModel):
    entity_type = Literal["PERSON", "PLACE", "TIME"]
    id: str


class Timeline(ConfiguredBaseModel):
    year: int
    count: int
    root_id: str


class Manifest(ConfiguredBaseModel):
    id: str
    citation_ids: List[str]
    timeline: List[Timeline]
