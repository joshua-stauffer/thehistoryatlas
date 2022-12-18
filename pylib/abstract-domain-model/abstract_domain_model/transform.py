from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Dict

from abstract_domain_model.errors import UnknownMessageError, MissingFieldsError
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
from abstract_domain_model.models.commands import CommandSuccess
from abstract_domain_model.models.commands.command_failed import (
    CommandFailed,
    CommandFailedPayload,
)
from abstract_domain_model.models.events.meta_tagged import (
    MetaTagged,
    MetaTaggedPayload,
)
from abstract_domain_model.types import Event, DomainObject, DomainObjectTypes


@dataclass
class TranslatorSpec:
    obj_cls: dataclass
    obj_payload: dataclass


class Translator:

    type_map = Dict[DomainObjectTypes, TranslatorSpec]

    def __init__(self):
        self._build_type_map()

    @classmethod
    def _build_type_map(cls) -> None:

        cls.type_map: Dict[DomainObjectTypes, TranslatorSpec] = {
            "SUMMARY_ADDED": TranslatorSpec(
                obj_cls=SummaryAdded,
                obj_payload=SummaryAddedPayload,
            ),
            "SUMMARY_TAGGED": TranslatorSpec(
                obj_cls=SummaryTagged,
                obj_payload=SummaryTaggedPayload,
            ),
            "CITATION_ADDED": TranslatorSpec(
                obj_cls=CitationAdded,
                obj_payload=CitationAddedPayload,
            ),
            "PERSON_ADDED": TranslatorSpec(
                obj_cls=PersonAdded,
                obj_payload=PersonAddedPayload,
            ),
            "PLACE_ADDED": TranslatorSpec(
                obj_cls=PlaceAdded,
                obj_payload=PlaceAddedPayload,
            ),
            "TIME_ADDED": TranslatorSpec(
                obj_cls=TimeAdded,
                obj_payload=TimeAddedPayload,
            ),
            "PERSON_TAGGED": TranslatorSpec(
                obj_cls=PersonTagged,
                obj_payload=PersonTaggedPayload,
            ),
            "PLACE_TAGGED": TranslatorSpec(
                obj_cls=PlaceTagged,
                obj_payload=PlaceTaggedPayload,
            ),
            "TIME_TAGGED": TranslatorSpec(
                obj_cls=TimeTagged,
                obj_payload=TimeTaggedPayload,
            ),
            "META_ADDED": TranslatorSpec(
                obj_cls=MetaAdded,
                obj_payload=MetaAddedPayload,
            ),
            "META_TAGGED": TranslatorSpec(
                obj_cls=MetaTagged, obj_payload=MetaTaggedPayload
            ),
            "COMMAND_FAILED": TranslatorSpec(
                obj_cls=CommandFailed,
                obj_payload=CommandFailedPayload,
            ),
            "COMMAND_SUCCESS": TranslatorSpec(obj_cls=CommandSuccess, obj_payload=None),
        }

    @classmethod
    def from_dict(cls, data: dict) -> DomainObject:
        """Transform a JSON dict into a known Domain Object."""

        data = deepcopy(data)
        type_ = data.get("type", None)
        translation_spec = cls.type_map.get(type_, None)
        if translation_spec is None:
            raise UnknownMessageError(data)

        try:
            return cls.resolve(data, translation_spec)

        except TypeError:
            # raised when the dataclass isn't provided with required fields
            raise MissingFieldsError(data)

    @staticmethod
    def resolve(data: dict, spec: TranslatorSpec) -> Event:
        payload = data.pop("payload", None)
        if payload is None:
            return spec.obj_cls(**data)
        payload = spec.obj_payload(**payload)
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def to_dict(domain_object: DomainObject):
        """Thin wrapper for dataclasses.asdict"""
        return asdict(domain_object)


Translator()
from_dict = Translator.from_dict
to_dict = Translator.to_dict
