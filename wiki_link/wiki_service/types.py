from dataclasses import dataclass
from typing import Literal, List
from pydantic import BaseModel

from wiki_service.models import GeoLocation, TimeDefinition

EntityType = Literal["PERSON", "PLACE", "TIME"]


@dataclass(frozen=True)
class WikiDataItem:
    url: str
    qid: str


class WikiTag(BaseModel):
    """Base class for wiki tags."""

    name: str
    wiki_id: str
    start_char: int
    stop_char: int


class PersonWikiTag(WikiTag):
    """A tag for a person."""

    pass


class PlaceWikiTag(WikiTag):
    """A tag for a place."""

    location: GeoLocation


class TimeWikiTag(WikiTag):
    """A tag for a time."""

    wiki_id: str | None
    time_definition: TimeDefinition


class WikiEvent(BaseModel):
    """A wiki event."""

    summary: str
    people_tags: List[PersonWikiTag]
    place_tag: PlaceWikiTag
    time_tag: TimeWikiTag
