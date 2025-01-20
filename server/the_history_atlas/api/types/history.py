from datetime import datetime
from typing import List, Union
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
    time: datetime
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
    stories: List[str] = []


class Story(BaseModel):
    id: UUID
    name: str
    events: List[HistoryEvent]
    index: int
