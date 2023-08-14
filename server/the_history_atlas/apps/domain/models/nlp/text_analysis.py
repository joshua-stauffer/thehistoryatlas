from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class TextBoundary(ConfiguredBaseModel):
    text: str
    start_char: int
    stop_char: int


class GeoResponse(ConfiguredBaseModel):
    # todo: rename, but this matches api
    longitude: float
    latitude: float
    geoshape: str | None = None


class TextAnalysis(ConfiguredBaseModel):
    text: str
    start_char: int
    stop_char: int
    guids: list[str]
    coords: list[GeoResponse]


class TextMap(ConfiguredBaseModel):
    PERSON: list[TextAnalysis]
    PLACE: list[TextAnalysis]
    TIME: list[TextAnalysis]


class TextAnalysisResponse(ConfiguredBaseModel):
    text_map: TextMap
    text: str
    boundaries: list[TextBoundary]


class GetTextAnalysis(ConfiguredBaseModel):
    text: str
