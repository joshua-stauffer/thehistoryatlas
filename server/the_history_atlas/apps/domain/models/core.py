from typing import List, Union, Literal

from pydantic import BaseModel


class Point(BaseModel):
    id: str
    latitude: float
    longitude: float
    name: str


class Location(Point):
    pass


class Source(BaseModel):
    id: str
    text: str
    title: str
    author: str
    publisher: str
    pubDate: str


class CalendarDate(BaseModel):
    time: str
    calendar: str
    precision: int


class Tag(BaseModel):
    id: str
    type: str
    startChar: int
    stopChar: int
    name: str
    defaultStoryId: str


class Map(BaseModel):
    locations: List[Location]


class HistoryEvent(BaseModel):
    id: str
    text: str
    lang: str
    date: CalendarDate
    source: Source
    tags: List[Tag]
    map: Map
    focus: Union[None, str] = None
    storyTitle: str
    stories: List[str] = []  # todo: story pointer, ID + name


class Story(BaseModel):
    id: str
    name: str
    events: List[HistoryEvent]
    index: int


class TagInput(BaseModel):
    name: str
    wikidata_id: str


class PersonInput(TagInput):
    type: Literal["person"] = "person"


class PlaceInput(TagInput):
    type: Literal["place"] = "place"
    latitude: float | None = None
    longitude: float | None = None
    geoshape: str | None


class TimeInput(TagInput):
    type: Literal["time"] = "time"
    time: str
    calendar_model: str
    precision: Literal[6, 7, 8, 9, 10, 11]
