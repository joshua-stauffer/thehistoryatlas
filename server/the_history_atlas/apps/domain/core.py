from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Precision = Literal[7, 8, 9, 10, 11]


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
    ...


class Person(PersonInput):
    id: UUID


class PlaceInput(WikiDataEntity):
    longitude: float
    latitude: float


class Place(PlaceInput):
    id: UUID


class TimeInput(WikiDataEntity):
    date: datetime
    precision: Precision
    calendar_model: str


class Time(TimeInput):
    id: UUID


class StoryOrder(BaseModel):
    tag_instance_id: UUID
    story_order: int
    datetime: datetime
    precision: Precision
