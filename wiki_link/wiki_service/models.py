"""Models used across the wiki service."""

from typing import Dict, List, Optional, Protocol
from pydantic import BaseModel


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
