from dataclasses import dataclass
from typing import Literal, Optional, Union, List


@dataclass(frozen=True)
class EntityAdded:
    transaction_id: str
    app_version: str
    timestamp: str
    user_id: str
    payload: Literal["NewPersonPayload", "NewPlacePayload", "NewTimePayload"]
    index: Optional[int]


@dataclass(frozen=True)
class NewPersonPayload:
    id: str
    name: str
    desc: Optional[str] = None
    wiki_link: Optional[str] = None
    lang: str = "en"
    # remote IDs
    wiki_data_id: Optional[str] = None
    modification_date: Optional[str] = None


@dataclass(frozen=True)
class NewPlacePayload:
    id: str
    name: str
    location: Union["Coordinates", "GeoShape"]
    lang: str = "en"

    desc: Optional[str] = None
    wiki_link: Optional[str] = None

    feature_class: Optional[str] = None
    feature_code: Optional[str] = None
    country_code: Optional[str] = None
    alternate_country_codes: Optional[List[str]] = None
    timezone: Optional[str] = None
    admin1_code: Optional[str] = None
    admin2_code: Optional[str] = None
    admin3_code: Optional[str] = None
    admin4_code: Optional[str] = None
    population: Optional[int] = None
    elevation: Optional[int] = None

    # remote IDs
    wiki_data_id: Optional[str] = None
    geo_names_id: Optional[str] = None
    modification_date: Optional[str] = None


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class GeoShape:
    geoshape: str


@dataclass(frozen=True)
class NewTimePayload:
    id: str
    name: str
    timestamp: str
    specificity: int
    calendar_type: str
    circa: bool = False
    latest: bool = False
    earliest: bool = False
    lang: str = "en"
    desc: Optional[str] = None
    wiki_link: Optional[str] = None

    # remote IDs
    wiki_data_id: Optional[str] = None
    modification_date: Optional[str] = None
