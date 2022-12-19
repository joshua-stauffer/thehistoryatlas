from enum import Enum
from typing import List, Optional

import strawberry


@strawberry.interface
class MutationResponse:
    success: bool
    message: Optional[str]
    token: str


@strawberry.type
class PublishCitationResponse(MutationResponse):
    success: bool
    message: Optional[str] = None
    token: str


@strawberry.input
class AnnotateCitationInput:
    citation: str
    citation_id: str
    summary: str
    summary_id: Optional[str]
    meta: "MetaDataInput"
    summary_tags: List["TagInput"]
    token: str


@strawberry.input
class MetaDataInput:
    id: Optional[str]
    author: str
    pageNum: Optional[int]
    pubDate: str
    publisher: str
    title: str


@strawberry.input
class TagInput:
    id: Optional[str]
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
