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
    token: str
    message: Optional[str]


@strawberry.input
class AnnotateCitationInput:
    citation: str
    citation_id: str
    summary: str
    meta: "MetaDataInput"
    summary_tags: List["TagInput"]
    token: str
    summary_id: Optional[str] = None


@strawberry.input
class MetaDataInput:
    author: strs
    pubDate: str
    publisher: str
    title: str
    pageNum: Optional[int] = None
    id: Optional[str] = None


@strawberry.input
class TagInput:
    name: str
    start_char: int
    stop_char: int
    type: "EntityType"
    geoshape: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    id: Optional[str] = None


@strawberry.enum
class EntityType(Enum):
    TIME = "TIME"
    PERSON = "PERSON"
    PLACE = "PLACE"
