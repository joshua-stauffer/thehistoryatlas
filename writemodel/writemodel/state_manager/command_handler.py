"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import logging
from copy import deepcopy
from dataclasses import asdict
from typing import Union, Dict, List, Optional
from uuid import uuid4

from abstract_domain_model.models import (
    CitationAdded,
    CitationAddedPayload,
    MetaAdded,
    MetaAddedPayload,
    SummaryTagged,
    SummaryTaggedPayload,
    SummaryAdded,
    SummaryAddedPayload,
    PersonAdded,
    PersonAddedPayload,
    PersonTagged,
    PersonTaggedPayload,
    TimeAdded,
    TimeAddedPayload,
    TimeTagged,
    TimeTaggedPayload,
    PlaceAdded,
    PlaceTagged,
    PlaceTaggedPayload,
    PlaceAddedPayload,
)
from abstract_domain_model.models.commands.add_person import AddPerson
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.models.commands.publish_citation import (
    PublishCitation,
    Time,
    Place,
    Person,
)
from abstract_domain_model.models.core import Name, Description
from abstract_domain_model.models.events.meta_tagged import (
    MetaTagged,
    MetaTaggedPayload,
)
from abstract_domain_model.transform import to_dict, from_dict
from abstract_domain_model.types import (
    Command,
    Event,
    PublishCitationType,
    CommandTypes,
)
from writemodel.state_manager.handler_errors import (
    CitationExistsError,
    NoValidatorError,
    MissingResourceError,
    ValidationError,
)
from writemodel.state_manager.handler_errors import GUIDError
from writemodel.state_manager.handler_errors import UnknownTagTypeError

log = logging.getLogger(__name__)

TAG_TYPES = {"PERSON", "PLACE", "TIME"}


class CommandHandler:
    """Class encapsulating logic to transform Commands from the user
    into canonical Events to be passed on to the Event Store."""

    def __init__(self, database_instance, hash_text):
        self._command_validators = self._map_command_validators()
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
        self._hashfunc = hash_text  # noqa

    def handle_command(self, command: Command) -> List[Event]:
        """Receives a dict, processes it, and returns an Event
        or raises an Exception"""
        log.debug(f"handling command {command}")
        self.validate_command(command)
        handler = self._command_handlers[command.type]
        events = handler(command)
        return events

    def validate_command(self, command: Command) -> bool:
        validate = self._command_validators.get(command.type, None)
        if validate is None:
            raise NoValidatorError
        return validate(command)

    def _map_command_handlers(self) -> Dict[CommandTypes, callable]:
        """Returns a dict of known commands mapping to their handle method."""
        return {
            "PUBLISH_CITATION": self.transform_publish_citation_to_events,
            "ADD_PERSON": self.transform_add_person,
            "ADD_TIME": self.transform_add_time,
            "ADD_PLACE": self.transform_add_place,
        }

    def _map_command_validators(self) -> Dict[CommandTypes, callable]:
        """Returns a dict of known commands mapping to their validator method."""
        return {
            "PUBLISH_CITATION": self.validate_publish_citation,
            "ADD_PERSON": self.validate_add_person,
            "ADD_TIME": self.validate_add_time,
            "ADD_PLACE": self.validate_add_place,
        }

    def transform_publish_citation_to_events(
        self, command: PublishCitation
    ) -> List[Event]:

        transaction_meta = {
            "transaction_id": str(uuid4()),
            "app_version": command.app_version,
            "timestamp": command.timestamp,
            "user_id": command.user_id,
        }

        # handle summary
        if command.payload.summary_id is not None:
            # tag existing summary
            summary = SummaryTagged(
                type="SUMMARY_TAGGED",
                **transaction_meta,
                payload=SummaryTaggedPayload(
                    id=command.payload.summary_id, citation_id=command.payload.id
                ),
            )
        else:
            # create a new summary
            summary = SummaryAdded(
                type="SUMMARY_ADDED",
                **transaction_meta,
                payload=SummaryAddedPayload(
                    id=str(uuid4()),
                    citation_id=command.payload.id,
                    text=command.payload.summary,
                ),
            )

        # summary ID on the command may be null - use the newly created event ID instead
        summary_id = summary.payload.id

        # handle meta
        if command.payload.meta.id is not None:
            # tag existing meta

            meta = MetaTagged(
                type="META_TAGGED",
                **transaction_meta,
                payload=MetaTaggedPayload(
                    id=command.payload.meta.id,
                    citation_id=command.payload.id,
                ),
            )
        else:
            # create a new meta
            kwargs = deepcopy(command.payload.meta.kwargs)

            pub_date = kwargs.pop("pubDate", None)
            meta = MetaAdded(
                type="META_ADDED",
                **transaction_meta,
                payload=MetaAddedPayload(
                    id=str(uuid4()),
                    citation_id=command.payload.id,
                    author=command.payload.meta.author,
                    title=command.payload.meta.title,
                    publisher=command.payload.meta.publisher,
                    pub_date=pub_date,
                    kwargs=command.payload.meta.kwargs,
                ),
            )

        # handle tags
        tags = [
            self.tag_to_event(
                tag=tag,
                transaction_meta=transaction_meta,
                citation_id=command.payload.id,
                summary_id=summary_id,
            )
            for tag in command.payload.tags
        ]

        # handle citation
        citation = CitationAdded(
            **transaction_meta,
            type="CITATION_ADDED",
            payload=CitationAddedPayload(
                id=command.payload.id,
                text=command.payload.text,
                summary_id=summary_id,
                meta_id=meta.payload.id,
                access_date=command.payload.meta.kwargs.pop("accessDate", None),
                page_num=command.payload.meta.kwargs.pop("pageNum", None),
            ),
        )

        return [summary, citation, *tags, meta]

    @staticmethod
    def tag_to_event(
        tag: Union[Person, Place, Time],
        transaction_meta: dict,
        citation_id: str,
        summary_id: str,
    ) -> Union[
        PersonAdded, PersonTagged, PlaceAdded, PlaceTagged, TimeAdded, TimeTagged
    ]:

        if isinstance(tag, Person):
            if tag.id is None:
                return PersonAdded(
                    type="PERSON_ADDED",
                    **transaction_meta,
                    payload=PersonAddedPayload(
                        id=str(uuid4()),
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                    ),
                )
            else:
                return PersonTagged(
                    type="PERSON_TAGGED",
                    **transaction_meta,
                    payload=PersonTaggedPayload(
                        id=tag.id,
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                    ),
                )

        elif isinstance(tag, Time):
            if tag.id is None:
                return TimeAdded(
                    type="TIME_ADDED",
                    **transaction_meta,
                    payload=TimeAddedPayload(
                        id=str(uuid4()),
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                    ),
                )
            else:
                return TimeTagged(
                    type="TIME_TAGGED",
                    **transaction_meta,
                    payload=TimeTaggedPayload(
                        id=tag.id,
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                    ),
                )

        elif isinstance(tag, Place):
            if tag.id is None:
                return PlaceAdded(
                    type="PLACE_ADDED",
                    **transaction_meta,
                    payload=PlaceAddedPayload(
                        id=str(uuid4()),
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                        latitude=tag.latitude,
                        longitude=tag.longitude,
                        geo_shape=tag.geo_shape,
                    ),
                )
            else:
                return PlaceTagged(
                    type="PLACE_TAGGED",
                    **transaction_meta,
                    payload=PlaceTaggedPayload(
                        id=tag.id,
                        name=tag.name,
                        citation_start=tag.start_char,
                        citation_end=tag.stop_char,
                        citation_id=citation_id,
                        summary_id=summary_id,
                    ),
                )

        else:
            raise UnknownTagTypeError(f"Received tag of unknown type `{tag}")

    def validate_publish_citation(self, command: PublishCitation) -> bool:

        # check text for uniqueness
        hashed_text = self._hashfunc(command.payload.text)
        if duplicate_id := self._db.check_citation_for_uniqueness(hashed_text):
            log.info("tried (and failed) to publish duplicate citation")
            raise CitationExistsError(duplicate_id)

        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=hashed_text, value=command.payload.id)

        # check summary id
        if command.payload.summary_id is not None:
            existing_type = self._db.check_id_for_uniqueness(command.payload.summary_id)
            if existing_type is None:
                raise MissingResourceError
            if existing_type != "SUMMARY":
                raise GUIDError(f"Summary id collided with id of type {existing_type}")

        # check tag ids
        for tag in command.payload.tags:
            if tag.id is None:
                # new tag, no need to validate
                continue
            existing_type = self._db.check_id_for_uniqueness(tag.id)
            if existing_type is None:
                raise MissingResourceError
            if tag.type != existing_type:
                raise GUIDError(
                    f"Tag id of type {tag.type} doesn't match database type of {existing_type}."
                )

        # check meta id
        if command.payload.meta.id is not None:
            existing_type = self._db.check_id_for_uniqueness(command.payload.meta.id)
            if existing_type is None:
                raise MissingResourceError
            if existing_type != "META":
                raise GUIDError(f"Meta id collided with id of type {existing_type}")

        return True

    def transform_add_person(self, command: AddPerson) -> PersonAdded:
        names = [
            Name(**asdict(name), id=str(uuid4())) for name in command.payload.names
        ]
        descriptions = [
            Description(**asdict(desc), id=str(uuid4()))
            for desc in command.payload.desc
        ]
        return PersonAdded(
            transaction_id=str(uuid4()),
            user_id=command.user_id,
            timestamp=command.timestamp,
            app_version=command.app_version,
            type="PERSON_ADDED",
            index=None,
            payload=PersonAddedPayload(
                id=str(uuid4()),
                names=names,
                desc=descriptions,
                wiki_link=command.payload.wiki_link,
                wiki_data_id=command.payload.wiki_data_id,
            ),
        )

    def validate_add_person(self, command) -> bool:
        for name in command.payload.names:
            self.validate_name(name=name)
        for description in command.payload.desc:
            self.validate_description(desc=description)
        self.validate_wiki_data_id(id=command.payload.wiki_data_id)
        return True

    def transform_add_place(self, command) -> PlaceAdded:
        ...

    def validate_add_place(self, command) -> bool:
        ...

    def transform_add_time(self, command) -> TimeAdded:
        ...

    def validate_add_time(self, command) -> bool:
        ...

    def validate_name(self, name: AddName) -> bool:
        self.validate_non_null_string(field=name.name, name="Name.name")
        self.validate_lang(field=name.lang, name="Name.lang")
        self.validate_nullable_string(field=name.start_time, name="Name.start_time")
        self.validate_nullable_string(field=name.end_time, name="Name.end_time")
        assert isinstance(name.is_historic, bool), "Name.is_historic must be a boolean."
        assert isinstance(name.is_default, bool), "Name.is_default must be a boolean."
        return True

    def validate_description(self, desc: AddDescription) -> bool:
        self.validate_non_null_string(field=desc.text, name="Description.text")
        self.validate_lang(field=desc.lang, name="Description.lang")
        self.validate_wiki_data_id(id=desc.wiki_data_id)
        return True

    @staticmethod
    def validate_lang(field: str, name: str) -> bool:
        if not isinstance(field, str) or len(field) != 2:
            raise ValidationError(f"{name} must be valid language code.")
        return True

    @staticmethod
    def validate_non_null_string(field: str, name) -> bool:
        if field is None or field == "":
            raise ValidationError(f"{name} must be non-null.")
        return True

    @staticmethod
    def validate_nullable_string(field: str, name) -> bool:
        if field is None:
            return True
        if field == "":
            raise ValidationError(f"{name} must be None or a valid string.")
        return True

    @staticmethod
    def validate_wiki_data_id(id: Optional[str]):
        if id is None:
            return True
        if len(id) < 2 or id[0] != "Q":
            raise ValidationError(f"Wikidata ID {id} is malformed.")
        return True
