from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import (
    EntitySummariesByName,
    GetEntitySummariesByName,
)


def resolve_get_entity_summaries_by_name(
    _: None, info: Info, name: str
) -> EntitySummariesByName:
    app = info.context.apps.readmodel_app

    entity_summaries_by_name = app.get_entity_summaries_by_name(
        query=GetEntitySummariesByName(name=name)
    )
    return entity_summaries_by_name
