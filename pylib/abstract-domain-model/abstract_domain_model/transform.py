from copy import deepcopy
from dataclasses import dataclass, asdict
from logging import getLogger
from typing import Dict, Optional, Callable

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
from abstract_domain_model.models.accounts import (
    GetUser,
    GetUserPayload,
    UserDetails,
    Credentials,
)
from abstract_domain_model.models.accounts.get_user import (
    GetUserResponse,
    GetUserResponsePayload,
)
from abstract_domain_model.models.commands import CommandSuccess
from abstract_domain_model.models.commands.add_person import AddPerson, AddPersonPayload
from abstract_domain_model.models.commands.add_place import AddPlacePayload, AddPlace
from abstract_domain_model.models.commands.add_time import AddTime, AddTimePayload
from abstract_domain_model.models.commands.command_failed import (
    CommandFailed,
    CommandFailedPayload,
)
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.models.core.description import Description
from abstract_domain_model.models.core.geo import Geo
from abstract_domain_model.models.events.meta_tagged import (
    MetaTagged,
    MetaTaggedPayload,
)
from abstract_domain_model.models.core.name import Name
from abstract_domain_model.models.core.time import Time
from abstract_domain_model.types import (
    Event,
    DomainObject,
    DomainObjectTypes,
    AccountEvent,
)

log = getLogger()


@dataclass
class TranslatorSpec:
    obj_cls: dataclass
    obj_payload: dataclass
    resolve_func: Optional[Callable[[Dict, "TranslatorSpec"], DomainObject]] = None


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
                resolve_func=cls.resolve_person_added,
            ),
            "PLACE_ADDED": TranslatorSpec(
                obj_cls=PlaceAdded,
                obj_payload=PlaceAddedPayload,
                resolve_func=cls.resolve_place_added,
            ),
            "TIME_ADDED": TranslatorSpec(
                obj_cls=TimeAdded,
                obj_payload=TimeAddedPayload,
                resolve_func=cls.resolve_time_added,
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
            "GET_USER": TranslatorSpec(
                obj_cls=GetUser,
                obj_payload=GetUserPayload,
                resolve_func=cls.resolve_account_event,
            ),
            "GET_USER_RESPONSE": TranslatorSpec(
                obj_cls=GetUserResponse,
                obj_payload=GetUserResponsePayload,
                resolve_func=cls.resolve_account_event,
            ),
            "ADD_PERSON": TranslatorSpec(
                obj_cls=AddPerson,
                obj_payload=AddPersonPayload,
                resolve_func=cls.resolve_add_person,
            ),
            "ADD_PLACE": TranslatorSpec(
                obj_cls=AddPlace,
                obj_payload=AddPlacePayload,
                resolve_func=cls.resolve_add_place,
            ),
            "ADD_TIME": TranslatorSpec(
                obj_cls=AddTime,
                obj_payload=AddTimePayload,
                resolve_func=cls.resolve_add_time,
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> DomainObject:
        """Transform a JSON dict into a known Domain Object."""
        log.info(f"Transforming dict: \n..\n{data}\n..\n")

        data = deepcopy(data)
        type_ = data.get("type", None)
        translation_spec = cls.type_map.get(type_, None)
        if translation_spec is None:
            raise UnknownMessageError(data)

        try:
            if translation_spec.resolve_func is not None:
                return translation_spec.resolve_func(data, translation_spec)
            else:
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
    def resolve_account_event(data: dict, spec: TranslatorSpec) -> AccountEvent:
        payload = data.pop("payload")
        user_details = payload.pop("user_details", None)
        if user_details is not None:
            payload["user_details"] = UserDetails(**user_details)
        credentials = payload.pop("credentials", None)
        if credentials is not None:
            payload["credentials"] = Credentials(**credentials)
        payload = spec.obj_payload(**payload)
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_time_added(data: Dict, spec: TranslatorSpec) -> TimeAdded:
        payload = data.pop("payload")
        time = payload.pop("time")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [Description(**d) for d in desc]
        names = payload.pop("names")
        payload = spec.obj_payload(
            **payload,
            desc=desc,
            time=Time(**time),
            names=[Name(**name) for name in names],
        )
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_place_added(data: Dict, spec: TranslatorSpec) -> PlaceAdded:
        payload = data.pop("payload")
        geo = payload.pop("geo")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [Description(**d) for d in desc]
        names = payload.pop("names")
        payload = spec.obj_payload(
            **payload, desc=desc, geo=Geo(**geo), names=[Name(**name) for name in names]
        )
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_person_added(data: Dict, spec: TranslatorSpec) -> PersonAdded:
        payload = data.pop("payload")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [Description(**d) for d in desc]
        names = payload.pop("names")
        payload = spec.obj_payload(
            **payload, desc=desc, names=[Name(**name) for name in names]
        )
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_add_time(data: Dict, spec: TranslatorSpec) -> AddTime:
        payload = data.pop("payload")
        time = payload.pop("time")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [AddDescription(**d) for d in desc]
        names = payload.pop("names")
        names = [AddName(**name) for name in names]
        payload = spec.obj_payload(
            **payload,
            desc=desc,
            time=Time(**time),
            names=names,
        )
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_add_place(data: Dict, spec: TranslatorSpec) -> AddPlace:
        payload = data.pop("payload")
        geo = payload.pop("geo")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [AddDescription(**d) for d in desc]
        names = payload.pop("names")
        names = [AddName(**name) for name in names]
        payload = spec.obj_payload(**payload, desc=desc, geo=Geo(**geo), names=names)
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def resolve_add_person(data: Dict, spec: TranslatorSpec) -> AddPerson:
        payload = data.pop("payload")
        desc = payload.pop("desc", None)
        if desc is not None:
            desc = [AddDescription(**d) for d in desc]
        names = payload.pop("names")
        names = [AddName(**name) for name in names]
        payload = spec.obj_payload(**payload, desc=desc, names=names)
        return spec.obj_cls(**data, payload=payload)

    @staticmethod
    def to_dict(domain_object: DomainObject):
        """Thin wrapper for dataclasses.asdict"""
        return asdict(domain_object)


Translator()
from_dict = Translator.from_dict
to_dict = Translator.to_dict
