from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetCitationByID(ConfiguredBaseModel):
    citation_id: str


class CitationMeta(ConfiguredBaseModel):
    accessDate: str
    pageNum: str


class Citation(ConfiguredBaseModel):
    id: str
    text: str
    meta: CitationMeta
    source_id: str
