from typing import List

from the_history_atlas.api.context import Info


def resolve_get_summaries_by_id(
    _: None, info: Info, summary_guids: List[str]
) -> List[str]:
    ...
