from dataclasses import dataclass
from typing import Literal


@dataclass
class DefaultEntity:
    id: str
    name: str
    type: Literal["PERSON", "PLACE", "TIME"]
