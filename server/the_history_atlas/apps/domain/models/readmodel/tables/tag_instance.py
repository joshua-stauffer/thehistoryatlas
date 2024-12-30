from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class TagInstanceModel(ConfiguredBaseModel):
    id: UUID
    start_char: int
    stop_char: int
    summary_id: UUID
    tag_id: UUID
