from uuid import UUID
from typing import Optional

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class TagInstanceInput(ConfiguredBaseModel):
    start_char: int
    stop_char: int
    summary_id: UUID
    tag_id: UUID
    story_order: Optional[int] = None


class TagInstanceModel(TagInstanceInput):
    id: UUID
