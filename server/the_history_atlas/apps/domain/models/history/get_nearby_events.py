from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class NearbyEventRow(ConfiguredBaseModel):
    event_id: UUID
    story_id: UUID
    person_name: str
    person_description: str | None
    summary_text: str | None
    place_name: str
    latitude: float
    longitude: float
    datetime: str
    precision: int
    calendar_model: str
