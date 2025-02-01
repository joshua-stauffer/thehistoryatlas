from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from the_history_atlas.apps.domain.core import Precision
from the_history_atlas.apps.domain.types import EntityType


class EventRow(BaseModel):
    event_id: UUID
    text: str
    source_id: UUID
    source_text: str
    source_title: str
    source_author: str
    source_publisher: str
    source_access_date: datetime


class TagRow(BaseModel):
    type: EntityType
    event_id: UUID
    tag_id: UUID
    start_char: int
    stop_char: int


class CalendarDateRow(BaseModel):
    event_id: UUID
    datetime: datetime
    calendar_model: str
    precision: Precision


class LocationRow(BaseModel):
    event_id: UUID
    tag_id: UUID
    latitude: float
    longitude: float


class TagNames(BaseModel):
    tag_id: UUID
    names: list[str]


class EventQuery(BaseModel):
    event_id: UUID
    event_row: EventRow
    tags: list[TagRow]
    calendar_date: CalendarDateRow
    location_row: LocationRow
    names: dict[UUID, TagNames]
