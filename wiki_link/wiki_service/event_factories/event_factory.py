from abc import ABC, abstractmethod
from typing import List, Protocol

from pydantic import BaseModel

from wiki_service.wikidata_query_service import (
    Entity,
    TimeDefinition,
    GeoLocation,
)


class WikiTag(BaseModel):
    name: str
    wiki_id: str
    start_char: int
    stop_char: int


class PersonWikiTag(WikiTag): ...


class PlaceWikiTag(WikiTag):
    location: GeoLocation


class TimeWikiTag(WikiTag):
    wiki_id: str | None
    time_definition: TimeDefinition


class WikiEvent(BaseModel):
    summary: str
    people_tags: List[PersonWikiTag]
    place_tag: PlaceWikiTag
    time_tag: TimeWikiTag


class UnprocessableEventError(Exception): ...


class Query(Protocol):
    def get_label(self, id: str, language: str) -> str: ...

    def get_geo_location(self, id: str) -> GeoLocation: ...


class EventFactory(ABC):
    def __init__(self, entity: Entity, query: Query) -> None:
        self._entity = entity
        self._query = query

    @property
    @abstractmethod
    def version(self) -> int: ...

    @property
    @abstractmethod
    def label(self) -> str: ...

    @abstractmethod
    def entity_has_event(self) -> bool: ...

    @abstractmethod
    def create_wiki_event(self) -> list[WikiEvent]: ...


_event_factories = []


def register_event_factory(cls: type[EventFactory]) -> type[EventFactory]:
    _event_factories.append(cls)
    return cls


def get_event_factories(entity: Entity, query: Query) -> list[EventFactory]:
    return [
        factory_class(entity=entity, query=query) for factory_class in _event_factories
    ]
