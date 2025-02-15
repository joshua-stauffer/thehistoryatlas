from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

from pydantic import BaseModel, Field

from wiki_service.wikidata_query_service import (
    CoordinateLocation,
    GeoshapeLocation,
    TimeDefinition,
)


class WikiTag(BaseModel):
    name: str
    wiki_id: str
    start_char: int
    stop_char: int


class PersonWikiTag(WikiTag):
    ...


class PlaceWikiTag(WikiTag):
    location: CoordinateLocation | GeoshapeLocation


class TimeWikiTag(WikiTag):
    wiki_id: str | None
    time: str
    precision: int
    calendar_model: str


class WikiEvent(BaseModel):
    summary: str
    people_tags: List[PersonWikiTag]
    place_tag: PlaceWikiTag
    time_tag: TimeWikiTag


class WikidataValue(BaseModel):
    type: str
    value: str
    # Not all fields have a datatype
    datatype: str | None = None
    # Use an alias for "xml:lang"
    xml_lang: str | None = Field(None, alias="xml:lang")


class UnprocessableEventError(Exception):
    ...




_QueryResult = TypeVar("_QueryResult", bound=BaseModel)


class EventFactory(ABC, Generic[_QueryResult]):

    @property
    @abstractmethod
    def version(self) -> int:
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        ...

    @abstractmethod
    def query(self, limit: int, offset: int) -> str:
        ...

    @property
    @abstractmethod
    def QueryResult(self) -> type[_QueryResult]:
        ...

    @abstractmethod
    def create_wiki_event(self, query_result: _QueryResult) -> WikiEvent:
        ...


_event_factories = []


def register_event_factory(cls: type[EventFactory]) -> type[EventFactory]:
    _event_factories.append(cls)
    return cls


def get_event_factories() -> list[EventFactory]:
    return _event_factories
