from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class SourceModelInput(ConfiguredBaseModel):
    title: str
    author: str
    publisher: str
    pub_date: str  # todo: make date
    kwargs: str  # json str


class SourceModel(SourceModelInput):
    id: UUID
