from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import (
    EntitySummary,
    GetEntitySummariesByIDs,
)


def resolve_get_entity_summaries_by_ids(
    _: None, info: Info, summary_guids: List[str]
) -> List[EntitySummary]:
    app = info.context.apps.readmodel_app

    entity_summaries = app.get_entity_summaries_by_ids(
        query=GetEntitySummariesByIDs(ids=summary_guids)
    )
    return entity_summaries
