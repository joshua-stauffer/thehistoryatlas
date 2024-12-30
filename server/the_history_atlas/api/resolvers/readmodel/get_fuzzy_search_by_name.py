from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import (
    FuzzySearchByName,
    GetFuzzySearchByName,
)


def resolve_get_fuzzy_search_by_name(
    _: None, info: Info, name: str
) -> List[FuzzySearchByName]:
    app = info.context.apps.readmodel_app

    fuzzy_search_by_name = app.get_fuzzy_search_by_name(
        query=GetFuzzySearchByName(name=name)
    )
    return fuzzy_search_by_name
