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
    tags: List[Union["Person", "Place", "Time"]]
    meta: "Meta"


@dataclass(frozen=True)
class Tag:
    id: str
    type: Literal["PERSON", "PLACE", "TIME"]
    start_char: int
    stop_char: int
    name: str


@dataclass(frozen=True)
class Person(Tag):
    type: Literal["PERSON"] = "PERSON"


@dataclass(frozen=True)
class Place(Tag):
    latitude: float
    longitude: float
    geo_shape: Optional[str] = None
    type: Literal["PLACE"] = "PLACE"


@dataclass(frozen=True)
class Time(Tag):
    type: Literal["TIME"] = "TIME"


@dataclass(frozen=True)
class Meta:
    author: str
    publisher: str
    title: str
    kwargs: dict
