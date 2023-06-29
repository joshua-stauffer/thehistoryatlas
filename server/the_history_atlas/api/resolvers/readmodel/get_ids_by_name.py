from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import EntitySummariesByName


def resolve_get_ids_by_name(_: None, info: Info, name: str) -> EntitySummariesByName:
    ...
