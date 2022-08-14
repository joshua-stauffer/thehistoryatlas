from abstract_domain_model.models import (
    TimeAdded,
    SummaryAdded,
    SummaryTagged,
    CitationAdded,
    PersonAdded,
    PlaceAdded,
    PersonTagged,
    PlaceTagged,
    TimeTagged,
    MetaAdded,
)
from abstract_domain_model.types import Model


type_map = {
    "SUMMARY_ADDED": SummaryAdded,
    "SUMMARY_TAGGED": SummaryTagged,
    "CITATION_ADDED": CitationAdded,
    "PERSON_ADDED": PersonAdded,
    "PLACE_ADDED": PlaceAdded,
    "TIME_ADDED": TimeAdded,
    "PERSON_TAGGED": PersonTagged,
    "PLACE_TAGGED": PlaceTagged,
    "TIME_TAGGED": TimeTagged,
    "META_ADDED": MetaAdded,
}


def from_dict(data: dict) -> Model:
    """Transform a JSON dict into a known Domain Object."""
    type = data["type"]
    return type_map[type](**data)
