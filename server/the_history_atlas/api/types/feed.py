from uuid import UUID

from pydantic import BaseModel


class FeedTag(BaseModel):
    id: UUID
    type: str
    name: str


class FeedTheme(BaseModel):
    slug: str
    name: str


class FeedEvent(BaseModel):
    summaryId: UUID
    summaryText: str
    tags: list[FeedTag]
    themes: list[FeedTheme]
    latitude: float | None = None
    longitude: float | None = None
    datetime: str | None = None
    precision: int | None = None
    isFavorited: bool = False


class FeedResponse(BaseModel):
    events: list[FeedEvent]
    nextCursor: str | None = None
