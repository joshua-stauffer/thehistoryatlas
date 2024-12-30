from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetFuzzySearchByName(ConfiguredBaseModel):
    name: str


class FuzzySearchByName(ConfiguredBaseModel):
    name: str
    ids: list[UUID]
