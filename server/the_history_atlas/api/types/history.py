from datetime import datetime
from typing import List, Union, Optional
from uuid import UUID

from pydantic import BaseModel


class Point(BaseModel):
    id: UUID
    latitude: float
    longitude: float
    name: str


class Source(BaseModel):
    id: UUID
    text: str
    title: str
    author: str
    publisher: str
    pubDate: datetime


class CalendarDate(BaseModel):
    datetime: str
    calendar: str
    precision: int


class Tag(BaseModel):
    id: UUID
    type: str
    startChar: int
    stopChar: int
    name: str
    defaultStoryId: UUID


class Map(BaseModel):
    locations: list[Point]


class HistoryEvent(BaseModel):
    id: UUID
    text: str
    lang: str
    date: CalendarDate
    source: Source
    tags: List[Tag]
    map: Map
    focus: Union[None, UUID] = None
    storyTitle: str
    description: str | None = None
    stories: List[str] = []


class Story(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    events: List[HistoryEvent]
    index: int


class TimeExistsRequest(BaseModel):
    datetime: str
    calendar_model: str
    precision: int


class TimeExistsResponse(BaseModel):
    id: UUID | None = None


class StorySearchResult(BaseModel):
    """A story search result containing the story's ID and name."""

    id: str
    name: str


class StorySearchResponse(BaseModel):
    """Response model for story search results."""

    results: List[StorySearchResult]
