from typing import List

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import EntitySummary


def resolve_get_entity_summaries_by_id(_: None, info: Info) -> List[EntitySummary]:
    ...
