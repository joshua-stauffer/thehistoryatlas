from enum import Enum
from typing import List, Optional

import strawberry


@strawberry.interface
class MutationResponse:
    success: bool
    message: Optional[bool]


@strawberry.type
class PublishCitationResponse(MutationResponse):
    success: bool
    message: Optional[bool] = None


@strawberry.input
class AnnotateCitationInput:
    citation: str
    citation_guid: str
    summary: str
    summary_guid: str
    meta: "MetaDataInput"
    summary_tags: List["TagInput"]


@strawberry.input
class MetaDataInput:
    GUID: str
    author: str
    pageNum: int
    pubDate: str
    publisher: str
    title: str


@strawberry.input
class TagInput:
    GUID: str
    name: str
    start_char: int
    stop_char: int
    type: "EntityType"
    geoshape: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@strawberry.enum
class EntityType(Enum):
    TIME = "TIME"
    PERSON = "PERSON"
    PLACE = "PLACE"
