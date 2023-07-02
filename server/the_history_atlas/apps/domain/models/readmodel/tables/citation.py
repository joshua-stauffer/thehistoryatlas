from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class CitationModel(ConfiguredBaseModel):
    id: UUID
    text: str
    source_id: UUID
    summary_id: UUID
    page_num: int
    access_date: str
