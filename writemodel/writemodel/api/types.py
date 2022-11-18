from enum import Enum
from typing import List, Optional, Literal

import strawberry


@strawberry.type
class Query:
    ...


@strawberry.type
class Mutation:
    @strawberry.mutation
    def PublishNewCitation(
        self, Annotation: "AnnotateCitationInput"
    ) -> Literal[str, str, bool]:
        return "test", "test", True


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
    geoshape: Optional[str]
    latitude: float
    longitude: float
    name: str
    start_char: int
    stop_char: int
    type: "EntityType"


@strawberry.enum
class EntityType(Enum):
    TIME = "TIME"
    PERSON = "PERSON"
    PLACE = "PLACE"
