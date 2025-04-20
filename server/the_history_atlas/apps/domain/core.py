from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Precision = Literal[7, 8, 9, 10, 11]


class StoryPointer(BaseModel):
    story_id: UUID
    event_id: UUID


class TagPointer(BaseModel):
    wikidata_id: str
    id: UUID | None = None


class TagInstance(BaseModel):
    id: UUID
    name: str
    start_char: int
    stop_char: int


class CitationInput(BaseModel):
    access_date: datetime
    wikidata_item_id: str
    wikidata_item_title: str
    wikidata_item_url: str


class WikiDataEntity(BaseModel):
    wikidata_id: str
    wikidata_url: str
    name: str


class PersonInput(WikiDataEntity):
    description: str | None = None


class Person(PersonInput):
    id: UUID


class PlaceInput(WikiDataEntity):
    longitude: float
    latitude: float
    description: str | None = None


class Place(PlaceInput):
    id: UUID


class TimeInput(WikiDataEntity):
    # times aren't guaranteed to have an ID in wikidata
    wikidata_id: str | None
    wikidata_url: str | None
    date: str
    precision: Precision
    calendar_model: str
    description: str | None = None


class Time(TimeInput):
    id: UUID


class StoryOrder(BaseModel):
    summary_id: UUID
    story_order: int | None = None
    datetime: str
    precision: Precision


class TagInstanceWithTime(BaseModel):
    id: UUID
    summary_id: UUID
    tag_id: UUID
    datetime: str
    precision: Precision
    after: list[UUID] | None


class TagInstanceWithTimeAndOrder(TagInstanceWithTime):
    story_order: int


class StoryName(BaseModel):
    name: str
    lang: str
    description: str | None = None


class Point(BaseModel):
    id: UUID
    latitude: float
    longitude: float
    name: str


class Source(BaseModel):
    id: UUID
    text: str
    title: str
    author: str
    publisher: str
    pub_date: datetime


class CalendarDate(BaseModel):
    datetime: str
    calendar: str
    precision: Precision


class Tag(BaseModel):
    id: UUID
    type: str
    start_char: int
    stop_char: int
    name: str
    default_story_id: UUID


class Map(BaseModel):
    locations: list[Point]


class HistoryEvent(BaseModel):
    id: UUID
    text: str
    lang: str
    date: CalendarDate
    source: Source
    tags: list[Tag]
    map: Map
    focus: UUID | None = None
    story_title: str
    description: str | None = None
    stories: list[str] = []


class Story(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    events: list[HistoryEvent]
