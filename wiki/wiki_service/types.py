from dataclasses import dataclass
from typing import Literal

EntityType = Literal["PERSON", "PLACE", "TIME"]
WikiType = Literal["WIKIDATA", "GEONAMES"]


@dataclass(frozen=True)
class WikiDataItem:
    url: str
    qid: str
