from abc import ABC, abstractmethod
from typing import Callable, List

from pydantic import BaseModel

from wiki_service.wikidata_query_service import (
    Entity,
    CoordinateLocation,
    GeoshapeLocation,
    TimeDefinition,
)


class WikiTag(BaseModel):
    name: str
    wiki_id: str
    start_char: int
    stop_char: int
    entity: Entity


class PersonWikiTag(WikiTag):
    ...


class PlaceWikiTag(WikiTag):
    location: CoordinateLocation | GeoshapeLocation


class TimeWikiTag(WikiTag):
    wiki_id: str | None
    time_definition: TimeDefinition
    entity: Entity | None


class WikiEvent(BaseModel):
    summary: str
    people_tags: List[PersonWikiTag]
    place_tag: PlaceWikiTag
    time_tag: TimeWikiTag


class UnprocessableEventError(Exception):
    ...


class EventFactory(ABC):
    def __init__(self, entity: Entity):
        self._entity = entity

    @property
    @abstractmethod
    def version(self) -> int:
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        ...

    @abstractmethod
    def entity_has_event(self) -> bool:
        ...

    @abstractmethod
    def supporting_entity_ids(self) -> list[str]:
        ...

    @abstractmethod
    def create_wiki_event(self, supporting_entities: dict[str, Entity]) -> WikiEvent:
        ...


_event_factories = []


def register_event_factory(cls: type[EventFactory]) -> type[EventFactory]:
    _event_factories.append(cls)
    return cls


def get_event_factories() -> list[EventFactory]:
    return _event_factories
