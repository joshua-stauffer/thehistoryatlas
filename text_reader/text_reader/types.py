from uuid import UUID

from pydantic import BaseModel


class ExtractedPerson(BaseModel):
    name: str
    description: str | None = None


class ExtractedPlace(BaseModel):
    name: str
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None


class ExtractedTime(BaseModel):
    name: str
    date: str
    calendar_model: str = "http://www.wikidata.org/entity/Q1985727"
    precision: int = 9


class ExtractedEvent(BaseModel):
    summary: str
    excerpt: str
    people: list[ExtractedPerson]
    place: ExtractedPlace
    time: ExtractedTime
    page_num: int | None = None
    confidence: float = 0.0


class ResolvedPerson(BaseModel):
    id: UUID
    name: str


class ResolvedPlace(BaseModel):
    id: UUID
    name: str
    latitude: float
    longitude: float


class ResolvedTime(BaseModel):
    id: UUID
    name: str
    date: str
    calendar_model: str
    precision: int


class ResolvedEvent(BaseModel):
    summary: str
    excerpt: str
    people: list[ResolvedPerson]
    place: ResolvedPlace
    time: ResolvedTime
    page_num: int | None = None
    confidence: float = 0.0
    is_duplicate: bool = False
    duplicate_has_wikidata: bool = False
    existing_summary_id: UUID | None = None
