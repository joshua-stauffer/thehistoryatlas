from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class WikiDataPersonInput(BaseModel):
    name: str
    wikidata_id: str
    wikidata_url: str


class WikiDataPersonOutput(WikiDataPersonInput):
    id: UUID


class WikiDataPlaceInput(BaseModel):
    name: str
    wikidata_id: str
    wikidata_url: str
    latitude: float
    longitude: float


class WikiDataPlaceOutput(WikiDataPlaceInput):
    id: UUID


class WikiDataTimeInput(BaseModel):
    name: str
    wikidata_id: str
    wikidata_url: str
    date: datetime
    precision: Literal[7, 8, 9, 10, 11]
    calendar_model: str


class WikiDataTimeOutput(WikiDataTimeInput):
    id: UUID


class WikiDataTagsInput(BaseModel):
    wikidata_ids: list[str]


class WikiDataTagPointer(BaseModel):
    wikidata_id: str
    id: UUID | None = None


class WikiDataTagsOutput(BaseModel):
    wikidata_ids: list[WikiDataTagPointer]
