from uuid import UUID

from pydantic import BaseModel


class ExtractedPerson(BaseModel):
    name: str
    full_name: str | None = None
    description: str | None = None


class ExtractedPlace(BaseModel):
    name: str  # natural form used verbatim in the summary (e.g. "New York")
    qualified_name: str | None = (
        None  # full form for disambiguation (e.g. "New York, New York")
    )
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
    name: str  # canonical name stored in DB
    summary_name: str  # form used in the summary text (for tag char-offset building)


class ResolvedPlace(BaseModel):
    id: UUID
    name: str  # canonical name stored in DB
    latitude: float
    longitude: float
    summary_name: str  # form used in the summary text (for tag char-offset building)


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
