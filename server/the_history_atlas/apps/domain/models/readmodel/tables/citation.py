from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class CitationModel(ConfiguredBaseModel):
    id: int
    guid: str
    text: str
    source_id: str  # uuid
    summary_id: int
    page_num: int
    access_date: str
