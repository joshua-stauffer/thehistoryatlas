from typing import List

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetFuzzySearchByName(ConfiguredBaseModel):
    name: str


class FuzzySearchByNameResults(ConfiguredBaseModel):
    name: str
    ids: frozenset[str]


class FuzzySearchByName(ConfiguredBaseModel):
    name: str
    results: List[FuzzySearchByNameResults]
