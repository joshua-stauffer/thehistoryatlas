from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel import Source


def resolve_search_sources(_: None, info: Info, searchTerm: str) -> List[Source]:
    app = info.context.apps.readmodel_app

    sources = app.get_sources_by_search_term(search_term=searchTerm)
    return sources
