from typing import List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetEntitySummariesByIDs(ConfiguredBaseModel):
    ids: List[str]
