from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class SummaryModel(ConfiguredBaseModel):

    id: int
    guid: str
    text: str
    time_tag: str
