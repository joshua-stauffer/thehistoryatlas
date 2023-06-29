from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import (
    Summary,
    GetSummariesByIDs,
)


def resolve_get_summaries_by_ids(
    _: None, info: Info, summary_guids: list[str]
) -> List[Summary]:
    app = info.context.apps.readmodel_app

    entity_summaries = app.get_summaries_by_ids(
        query=GetSummariesByIDs(summary_ids=summary_guids)
    )
    return entity_summaries
