from typing import Literal, List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel
from the_history_atlas.apps.domain.types import EntityType


class GetManifest(ConfiguredBaseModel):
    entity_type = EntityType
    id: str


class Timeline(ConfiguredBaseModel):
    year: int
    count: int
    root_id: str


class Manifest(ConfiguredBaseModel):
    id: str
    citation_ids: List[str]
    timeline: List[Timeline]
