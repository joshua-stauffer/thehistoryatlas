from typing import List, Literal

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class MetaDataInput(ConfiguredBaseModel):
    author: str
    pubDate: str
    publisher: str
    title: str
    pageNum: int | None = None
    accessDate: str | None = None
    id: str | None = None


class TagInput(ConfiguredBaseModel):
    name: str
    startChar: int
    stopChar: int
    type: Literal["TIME", "PLACE", "PERSON"]
    geoshape: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    id: str | None = None


class AnnotateCitationInput(ConfiguredBaseModel):
    citation: str
    citationId: str
    summary: str
    meta: MetaDataInput
    summaryTags: List[TagInput]
    token: str
    summaryId: str | None = None
