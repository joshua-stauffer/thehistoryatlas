"""Models and types used across the wiki service."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Literal
from pydantic import BaseModel

from wiki_service.wikidata_query_service import WikiDataQueryService

EntityType = Literal["PERSON", "PLACE", "TIME", "WORK_OF_ART", "BOOK"]


class Property(BaseModel):
    language: str
    value: str


class Entity(BaseModel):
    """Expected fields on a wikidata entity"""

    id: str
    pageid: int
    ns: int
    title: str
    lastrevid: int
    modified: str
    type: str
    labels: Dict[str, Property]
    descriptions: Dict[str, Property]
    aliases: Dict[str, List[Property]]
    claims: Dict[str, List[Dict]]
    sitelinks: Dict[str, Dict]


class CoordinateLocation(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    latitude: float
    longitude: float
    altitude: Optional[int]
    precision: Optional[float]
    globe: str


class GeoshapeLocation(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    url: str
    zoom: int
    latitude: float
    longitude: float
    data: Dict


class GeoLocation(BaseModel):
    coordinates: CoordinateLocation | None
    geoshape: GeoshapeLocation | None


class TimeDefinition(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    time: str
    timezone: int
    before: int
    after: int
    precision: int
    calendarmodel: str


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


Query = WikiDataQueryService
