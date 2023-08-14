from enum import Enum

import strawberry


@strawberry.type
class DefaultEntity:
    id: str
    type: "EntityType"
    name: str


@strawberry.enum
class EntityType(Enum):
    TIME = "TIME"
    PERSON = "PERSON"
    PLACE = "PLACE"


@strawberry.type
class Source:
    id: str
    title: str
    author: str
    publisher: str
    pub_date: str
