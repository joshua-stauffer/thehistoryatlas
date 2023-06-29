from typing import List, Literal, Annotated

from pydantic import Field

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class GetSummariesByIDs(ConfiguredBaseModel):
    summary_ids: List[str]


class Person(ConfiguredBaseModel):
    id: str
    type: Literal["PERSON"]
    start_char: int
    stop_char: int
    names: List[str]


class Place(ConfiguredBaseModel):
    id: str
    type: Literal["PLACE"]
    start_char: int
    stop_char: int
    names: List[str]
    latitude: float | None
    longitude: float | None
    geoshape: str | None = None


class Time(ConfiguredBaseModel):
    id: str
    type: Literal["PERSON"]
    start_char: int
    stop_char: int
    name: str


Tag = Annotated[Person, Place, Time, Field(discriminator="type")]


class Summary(ConfiguredBaseModel):
    id: str
    text: str
    tags: List[Tag]
    citation_ids: List[str]
