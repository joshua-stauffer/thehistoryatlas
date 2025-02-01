from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class SummaryModel(ConfiguredBaseModel):

    id: UUID
    text: str
    time_tag: str  # todo: delete
