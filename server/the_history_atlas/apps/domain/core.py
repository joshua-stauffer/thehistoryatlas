from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


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
    precision: Literal[7, 8, 9, 10, 11]
    calendar_model: str


class Time(TimeInput):
    id: UUID
