from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class WikiDataPersonInput(BaseModel):
    name: str
    wikidata_id: str
    wikidata_url: str
    description: str | None = None


class WikiDataPersonOutput(WikiDataPersonInput):
    id: UUID


class WikiDataPlaceInput(BaseModel):
    name: str
    wikidata_id: str
    wikidata_url: str
    latitude: float
    longitude: float
    description: str | None = None


class WikiDataPlaceOutput(WikiDataPlaceInput):
    id: UUID


class WikiDataTimeInput(BaseModel):
    name: str
    wikidata_id: str | None
    wikidata_url: str | None
    date: str
    precision: Literal[7, 8, 9, 10, 11]
    calendar_model: str
    description: str | None = None


class WikiDataTimeOutput(WikiDataTimeInput):
    id: UUID


class WikiDataTagsInput(BaseModel):
    wikidata_ids: list[str]


class WikiDataTagPointer(BaseModel):
    wikidata_id: str
    id: UUID | None = None


class WikiDataTagsOutput(BaseModel):
    wikidata_ids: list[WikiDataTagPointer]


class TagInput(BaseModel):
    id: UUID
    name: str
    start_char: int
    stop_char: int


class WikiDataCitationInput(BaseModel):
    access_date: datetime
    wikidata_item_id: str
    wikidata_item_title: str
    wikidata_item_url: str


class WikiDataEventInput(BaseModel):
    summary: str
    tags: list[TagInput]
    citation: WikiDataCitationInput
    after: list[UUID]


class WikiDataEventOutput(BaseModel):
    id: UUID
