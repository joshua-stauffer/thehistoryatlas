from dataclasses import dataclass
from typing import Literal, List, Optional, Union


@dataclass(frozen=True)
class PublishCitation:

    user_id: str
    timestamp: str
    app_version: str
    payload: "PublishCitationPayload"
    type: Literal["PUBLISH_CITATION"] = "PUBLISH_CITATION"


@dataclass(frozen=True)
class PublishCitationPayload:
    id: str
    text: str
    summary: Optional[str]  # won't exist when tagging a summary
    summary_id: Optional[str]
    tags: List[Union["Person", "Place", "Time"]]
    meta: "Meta"


@dataclass(frozen=True)
class Tag:
    id: Optional[str]
    type: Literal["PERSON", "PLACE", "TIME"]
    start_char: int
    stop_char: int
    name: str


@dataclass(frozen=True)
class Person(Tag):
    type: Literal["PERSON"]


@dataclass(frozen=True)
class Place(Tag):
    latitude: float
    longitude: float
    geo_shape: Optional[str]
    type: Literal["PLACE"]


@dataclass(frozen=True)
class Time(Tag):
    type: Literal["TIME"]


@dataclass(frozen=True)
class Meta:
    id: Optional[str]
    author: str
    publisher: str
    title: str
    kwargs: dict
