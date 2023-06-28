from typing import List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel
from the_history_atlas.apps.domain.models.readmodel.queries import EntitySummary


class GetEntitySummariesByName(ConfiguredBaseModel):
    name: str


class EntitySummariesByNameResult(ConfiguredBaseModel):
    ids: List[str]
    summaries: List[EntitySummary]
