from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.readmodel.queries import Manifest
from the_history_atlas.apps.domain.types import EntityType


def resolve_get_manifest(
    _: None, info: Info, entityType: EntityType, GUID: str
) -> Manifest:
    ...
