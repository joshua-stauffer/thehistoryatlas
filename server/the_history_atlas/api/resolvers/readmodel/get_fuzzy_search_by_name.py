from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import FuzzySearchByName


def resolve_get_fuzzy_search_by_name(
    _: None, info: Info, name: str
) -> List[FuzzySearchByName]:
    ...
