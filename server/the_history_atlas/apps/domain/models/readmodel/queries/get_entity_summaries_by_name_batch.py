from typing import List, Dict

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel
from the_history_atlas.apps.domain.models.readmodel.queries import EntitySummary


class GetEntityIDsByNames(ConfiguredBaseModel):
    names: List[str]


class EntityIDsByNamesResult(ConfiguredBaseModel):
    names: Dict[str, List[str]]
