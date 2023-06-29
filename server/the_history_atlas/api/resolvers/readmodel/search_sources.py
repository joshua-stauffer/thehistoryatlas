from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel import Source


def resolve_search_sources(_: None, info: Info, searchTerm: str) -> List[Source]:
    ...
