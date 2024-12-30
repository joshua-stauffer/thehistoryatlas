from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class TagNameAssocModel(ConfiguredBaseModel):
    tag_id: UUID
    name_id: UUID
