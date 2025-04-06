"""Models and types used across the wiki service."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Literal
from pydantic import BaseModel

EntityType = Literal["PERSON", "PLACE", "TIME", "WORK_OF_ART", "BOOK", "ORATION"]


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


class LocationResult(BaseModel):
    name: str
    id: str
    geo_location: GeoLocation


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


class Query(Protocol):
    """Protocol for querying Wikidata."""

    def get_entity(self, id: str) -> Entity:
        """Get an entity by ID."""
        ...

    def get_label(self, id: str, language: str) -> str:
        """Get an entity's label in the specified language."""
        ...

    def get_description(self, id: str, language: str) -> Optional[str]:
        """Get an entity's description in the specified language."""
        ...

    def get_geo_location(self, id: str) -> GeoLocation:
        """Get an entity's location."""
        ...

    def get_time_definition_from_entity(
        self, entity: Entity, claim: str, time_props: list[str]
    ) -> Optional[TimeDefinition]: ...

    def get_time_definition_from_claim(
        self, claim: dict, time_props: list[str]
    ) -> TimeDefinition | None: ...

    def get_location_from_claim(
        self, claim: dict, location_props: list[str]
    ) -> LocationResult | None: ...

    def get_location_from_entity(
        self, entity: Entity, claim_props: list[str]
    ) -> LocationResult | None: ...
