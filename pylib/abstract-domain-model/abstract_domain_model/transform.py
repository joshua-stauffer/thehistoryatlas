from copy import deepcopy

from abstract_domain_model.errors import UnknownMessageError
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
    SummaryAddedPayload,
    SummaryTaggedPayload,
    CitationAddedPayload,
    PersonAddedPayload,
    PlaceAddedPayload,
    TimeAddedPayload,
    PersonTaggedPayload,
    PlaceTaggedPayload,
    TimeTaggedPayload,
    MetaAddedPayload,
)
from abstract_domain_model.types import Model


type_map = {
    "SUMMARY_ADDED": (SummaryAdded, SummaryAddedPayload),
    "SUMMARY_TAGGED": (SummaryTagged, SummaryTaggedPayload),
    "CITATION_ADDED": (CitationAdded, CitationAddedPayload),
    "PERSON_ADDED": (PersonAdded, PersonAddedPayload),
    "PLACE_ADDED": (PlaceAdded, PlaceAddedPayload),
    "TIME_ADDED": (TimeAdded, TimeAddedPayload),
    "PERSON_TAGGED": (PersonTagged, PersonTaggedPayload),
    "PLACE_TAGGED": (PlaceTagged, PlaceTaggedPayload),
    "TIME_TAGGED": (TimeTagged, TimeTaggedPayload),
    "META_ADDED": (MetaAdded, MetaAddedPayload),
}


def from_dict(data: dict) -> Model:
    """Transform a JSON dict into a known Domain Object."""

    data = deepcopy(data)

    type_ = data.get("type", None)
    cls, payload_cls = type_map.get(type_, (None, None))
    if type_ is None or cls is None:
        raise UnknownMessageError(data)

    payload = data.pop("payload", None)
    if payload is None:
        return cls(**data)

    typed_payload = payload_cls(**payload)
    return cls(**data, payload=typed_payload)
