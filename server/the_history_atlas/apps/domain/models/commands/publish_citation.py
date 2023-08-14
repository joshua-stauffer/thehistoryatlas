from dataclasses import dataclass
from typing import Literal, List, Optional, Union
from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class MetaKwargs(ConfiguredBaseModel):
    pageNum: int | None = None
    pubDate: str | None = None
    accessDate: str | None = None


class Meta(ConfiguredBaseModel):
    id: str | None
    author: str
    publisher: str
    title: str
    kwargs: MetaKwargs


class Tag(ConfiguredBaseModel):
    id: str | None = None
    type: Literal["PERSON", "PLACE", "TIME"]
    start_char: int
    stop_char: int
    name: str


class Person(Tag):
    type: Literal["PERSON"]


class Place(Tag):
    latitude: float | None = None
    longitude: float | None = None
    geo_shape: str | None = None
    type: Literal["PLACE"]


class Time(Tag):
    type: Literal["TIME"]


class PublishCitationPayload(ConfiguredBaseModel):
    id: str  # ensure duplicate citations aren't processed
    text: str
    summary: str | None  # won't exist when tagging a summary
    summary_id: str | None = None  # won't exist when creating new summary
    tags: List[Union[Person, Place, Time]]
    meta: Meta
    token: str


class PublishCitation(ConfiguredBaseModel):

    user_id: str
    timestamp: str
    app_version: str
    payload: PublishCitationPayload
    type: Literal["PUBLISH_CITATION"] = "PUBLISH_CITATION"


class PublishCitationResponse(ConfiguredBaseModel):
    success: bool
    token: str
    message: str | None
