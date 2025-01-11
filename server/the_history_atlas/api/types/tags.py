from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class WikiDataPersonInput(BaseModel):
    names: list[str]
    wikidata_id: UUID
    wikidata_url: str


class WikiDataPersonOutput(BaseModel):
    id: UUID


class WikiDataPlaceInput(BaseModel):
    names: list[str]
    wikidata_id: UUID
    wikidata_url: str
    latitude: float
    longitude: float


class WikiDataPlaceOutput(BaseModel):
    id: UUID


class WikiDataTimeInput(BaseModel):
    names: list[str]
    wikidata_id: UUID
    wikidata_url: str
    date: datetime
    precision: Literal[7, 8, 9, 10, 11]
    calendar_model: str


class WikiDataTimeOutput(BaseModel):
    id: UUID
