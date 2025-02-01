from typing import List, Dict

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetEntityIDsByNames(ConfiguredBaseModel):
    names: List[str]


class EntityIDsByNames(ConfiguredBaseModel):
    names: Dict[str, List[str]]
