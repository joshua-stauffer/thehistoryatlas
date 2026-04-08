from typing import Literal
from uuid import UUID

from pydantic import BaseModel


# --- Source ---


class TextReaderSourceInput(BaseModel):
    title: str
    author: str
    publisher: str
    pub_date: str | None = None
    pdf_page_offset: int = 0


class TextReaderSourceOutput(BaseModel):
    id: UUID
    title: str
    author: str
    publisher: str
    pub_date: str | None = None
    pdf_page_offset: int = 0


# --- Person ---


class TextReaderPersonInput(BaseModel):
    name: str
    description: str | None = None


class TextReaderPersonOutput(BaseModel):
    id: UUID
    name: str
    description: str | None = None


# --- Place ---


class TextReaderPlaceInput(BaseModel):
    name: str
    latitude: float
    longitude: float
    geonames_id: int | None = None
    description: str | None = None


class TextReaderPlaceOutput(BaseModel):
    id: UUID
    name: str
    latitude: float
    longitude: float
    geonames_id: int | None = None
    description: str | None = None


# --- Time ---


class TextReaderTimeInput(BaseModel):
    name: str
    date: str
    calendar_model: str
    precision: Literal[6, 7, 8, 9, 10, 11]
    description: str | None = None


class TextReaderTimeOutput(BaseModel):
    id: UUID
    name: str
    date: str
    calendar_model: str
    precision: int
    description: str | None = None


# --- Event ---


class TextReaderTagInput(BaseModel):
    id: UUID
    name: str
    start_char: int
    stop_char: int


class TextReaderCitationInput(BaseModel):
    text: str
    page_num: int | None = None
    access_date: str | None = None


class TextReaderEventInput(BaseModel):
    summary: str
    tags: list[TextReaderTagInput]
    citation: TextReaderCitationInput
    source_id: UUID
    story_id: UUID
    canonical_summary_id: UUID | None = None
    theme_slugs: list[str] = []


class TextReaderEventOutput(BaseModel):
    id: UUID


# --- Story ---


class TextReaderStoryInput(BaseModel):
    name: str
    description: str | None = None
    source_id: UUID | None = None


class TextReaderStoryOutput(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    source_id: UUID | None = None


# --- Search Results ---


class PersonSearchCandidate(BaseModel):
    id: UUID
    name: str
    type: str
    description: str | None = None
    earliest_date: str | None = None
    latest_date: str | None = None


class PeopleSearchResult(BaseModel):
    candidates: list[PersonSearchCandidate]


class PlaceSearchCandidate(BaseModel):
    id: UUID
    name: str
    latitude: float | None = None
    longitude: float | None = None


class PlaceSearchResult(BaseModel):
    candidates: list[PlaceSearchCandidate]


# --- Summary Match ---


class SummaryMatchResult(BaseModel):
    found: bool
    summary_id: UUID | None = None
    summary_text: str | None = None
    has_wikidata_citation: bool = False
