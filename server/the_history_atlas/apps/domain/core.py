from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class TagPointer(BaseModel):
    wikidata_id: str
    id: UUID | None = None


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
