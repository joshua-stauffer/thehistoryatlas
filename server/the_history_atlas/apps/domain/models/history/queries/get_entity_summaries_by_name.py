from typing import List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel
from the_history_atlas.apps.domain.models.history.queries.entity_summary import (
    EntitySummary,
)


class GetEntitySummariesByName(ConfiguredBaseModel):
    name: str


class EntitySummariesByName(ConfiguredBaseModel):
    ids: List[str]
    summaries: List[EntitySummary]
