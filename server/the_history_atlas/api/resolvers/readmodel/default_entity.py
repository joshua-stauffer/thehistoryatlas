from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel import DefaultEntity


def resolve_default_entity(_: None, info: Info) -> DefaultEntity:
    app = info.context.apps.readmodel_app

    default_entity = app.get_default_entity()
    return default_entity
