from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class Geo:
    """
    Canonical representation of a geographic place.
    """

    latitude: float
    longitude: float
    geoshape: Optional[str] = None
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
