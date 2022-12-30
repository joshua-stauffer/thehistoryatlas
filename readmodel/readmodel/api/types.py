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
