"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import logging
from copy import deepcopy
from dataclasses import asdict
from typing import Any, Union, Dict, List, Literal
from uuid import uuid4

from abstract_domain_model.models import CitationAdded, CitationAddedPayload
from abstract_domain_model.models.commands.publish_citation import (
    PublishCitation,
    PublishCitationPayload,
    Meta,
    Time,
    Place,
    Person,
)
from abstract_domain_model.types import Command, Event, PublishCitationType
from writemodel.state_manager.handler_errors import (
    CitationExistsError,
    NoValidatorError,
    MissingResourceError,
)
from writemodel.state_manager.handler_errors import UnknownCommandTypeError
from writemodel.state_manager.handler_errors import CitationMissingFieldsError
from writemodel.state_manager.handler_errors import GUIDError
from writemodel.state_manager.handler_errors import UnknownTagTypeError
from writemodel.state_manager.event_composer import EventComposer

log = logging.getLogger(__name__)

TAG_TYPES = {"PERSON", "PLACE", "TIME"}


class CommandHandler:
    """Class encapsulating logic to transform Commands from the user
    into canonical Events to be passed on to the Event Store."""

    def __init__(self, database_instance, hash_text):
        self._translators = self._map_translators()
        self._command_validators = self._map_command_validators()
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
        self._hashfunc = hash_text  # noqa

    def handle_command(self, command: Dict):
        """Receives a dict, processes it, and returns an Event
        or raises an Exception"""
        log.debug(f"handling command {command}")
        command: Command = self.translate_command(command)
        handler = self._command_handlers[type(command)]
        events = handler(command)
        return [asdict(event) for event in events]

    def translate_command(self, command: dict) -> Command:
        log.debug(f"translating command {command}")
        type_ = command.get("type")
        translator = self._translators.get(type_, None)
        if translator is None:
            raise UnknownCommandTypeError
        try:
            return translator(command)
        except KeyError as e:
            raise CitationMissingFieldsError(e)

    def validate_command(self, command: Command) -> bool:
        validate = self._command_validators.get(type(command), None)
        if validate is None:
            raise NoValidatorError
        return validate(command)

    def _map_command_handlers(self) -> Dict[type, callable]:
        """Returns a dict of known commands mapping to their handle method."""
        return {
            PublishCitationType: self._transform_publish_citation_to_events,
        }

    def _map_command_validators(self) -> Dict[type, callable]:
        """Returns a dict of known commands mapping to their validator method."""
        return {
            PublishCitationType: self._validate_publish_citation,
        }

    def _map_translators(self) -> Dict[str, callable]:
        return {"PUBLISH_NEW_CITATION": self._translate_publish_citation}

    def _transform_publish_citation_to_events(
        self, command: PublishCitation
    ) -> List[Event]:

        events = []
        transaction_meta = {
            "transaction_id": str(uuid4()),
            "app_version": command.app_version,
            "timestamp": command.timestamp,
            "user_id": command.user_id,
        }

        citation = CitationAdded(
            **transaction_meta,
            type="CITATION_ADDED",
            payload=CitationAddedPayload(
                id=command.payload.id,
                text=command.payload.text,
                summary_id=command.payload.summary_id,
                meta_id=command.payload.meta.id,
            ),
        )

        return events

    def _translate_publish_citation(self, command: dict) -> PublishCitation:
        """
        Transform a dict version of the the JSON command PUBLISH_NEW_CITATION
        into ADM objects.
        """
        command = deepcopy(command)
        id_ = str(uuid4())
        user_id = command["user"]
        timestamp = command["timestamp"]
        app_version = command["app_version"]
        text = command["payload"]["text"]
        tags = [self._translate_tag(tag) for tag in command["payload"]["tags"]]
        author = command["payload"]["meta"]["author"]
        publisher = command["payload"]["meta"]["publisher"]
        title = command["payload"]["meta"]["title"]
        meta_id = command["payload"]["meta"].get("GUID", None)
        summary = command["payload"]["summary"]
        summary_id = command["payload"].get("summary_guid", None)
        kwargs = {
            key: value
            for key, value in command["payload"]["meta"].items()
            if key not in ("author", "publisher", "title")
        }
        return PublishCitation(
            user_id=user_id,
            timestamp=timestamp,
            app_version=app_version,
            payload=PublishCitationPayload(
                id=id_,
                text=text,
                tags=tags,
                summary=summary,
                summary_id=summary_id,
                meta=Meta(
                    id=meta_id,
                    author=author,
                    publisher=publisher,
                    title=title,
                    kwargs=kwargs,
                ),
            ),
        )

    def _translate_tag(self, tag: dict) -> Union[Person, Place, Time]:
        """Build typed dataclass from incoming request."""
        type_ = tag.get("type")
        if type_ == "PERSON":
            return self._translate_person(tag)
        elif type_ == "TIME":
            return self._translate_time(tag)
        elif type_ == "PLACE":
            return self._translate_place(tag)
        else:
            raise UnknownTagTypeError(f"Received unknown tag type: {type_}")

    def _translate_person(self, tag) -> Person:
        type_: Literal["PERSON"] = "PERSON"
        id_ = tag.get("GUID", None)
        name = tag["name"]
        start_char = tag["start_char"]
        stop_char = tag["stop_char"]
        return Person(
            id=id_, name=name, start_char=start_char, stop_char=stop_char, type=type_
        )

    def _translate_place(self, tag) -> Place:
        type_: Literal["PLACE"] = "PLACE"
        id_ = tag.get("GUID", None)
        name = tag["name"]
        start_char = tag["start_char"]
        stop_char = tag["stop_char"]
        latitude = tag["latitude"]
        longitude = tag["longitude"]
        geo_shape = tag.get("geoshape", None)
        return Place(
            id=id_,
            type=type_,
            name=name,
            start_char=start_char,
            stop_char=stop_char,
            latitude=latitude,
            longitude=longitude,
            geo_shape=geo_shape,
        )

    def _translate_time(self, tag) -> Time:
        type_: Literal["TIME"] = "TIME"
        id_ = tag.get("GUID", None)
        name = tag["name"]
        start_char = tag["start_char"]
        stop_char = tag["stop_char"]
        return Time(
            id=id_, name=name, start_char=start_char, stop_char=stop_char, type=type_
        )

    def _validate_publish_citation(self, command: PublishCitation) -> bool:

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

    def _handle_publish_new_citation_old(self, cmd):
        """Handles the PUBLISH_NEW_CITATION command.

        Validates the command's contents and returns a synthetic event
        or raises an error.

        Raises a CitationMissingFieldsError if a field of the command
            is not present.
        Raises a CitationExistsError error if text is not unique.
        Raises a GUIDError if any of the new GUIDs are not unique,
            or if any of the existing GUIDs don't match type.
        Raises a UnknownTagTypeError if an unknown tag is passed.
        """
        # a wrapper for handling new citations
        # provides a useful error if the command dict is missing fields
        try:
            return self.__handle_publish_new_citation(cmd)
        except KeyError as e:
            raise CitationMissingFieldsError(e)

    # utility methods

    def __handle_publish_new_citation(self, cmd):
        """logic for handle_publish_new_citations"""

        log.info(f"CommandHandler: received a new citation: {cmd}")
        # extract fields from command
        user = cmd["user"]
        timestamp = cmd["timestamp"]
        app_version = cmd["app_version"]
        citation_guid = cmd["payload"]["citation_guid"]
        tags = cmd["payload"]["summary_tags"]
        meta = cmd["payload"]["meta"]
        summary_text = cmd["payload"]["summary"]
        summary_guid = cmd["payload"]["summary_guid"]

        composer = EventComposer(
            transaction_guid=str(uuid4()),
            app_version=app_version,
            user=user,
            timestamp=timestamp,
        )

        # validate that this text is unique
        text = cmd["payload"]["citation"]
        hashed_text = self._hashfunc(text)
        log.debug(f"Text hash is {hashed_text}")
        if hash_guid := self._db.check_citation_for_uniqueness(hashed_text):
            log.info("tried (and failed) to publish duplicate citation")
            raise CitationExistsError(hash_guid)
        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=hashed_text, value=citation_guid)

        # check citation GUID
        if cit_res := self._db.check_id_for_uniqueness(citation_guid):
            raise GUIDError(
                "Citation GUID was not unique. "
                + f"Collided with GUID of type {cit_res}"
            )
        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=citation_guid, value="CITATION")

        # check tag GUIDs. if they match, ensure that they are labeled correctly
        # tags will be added to composer by type during validation
        tag_guids = self.__parse_tags(tags, summary_guid, composer)

        # check meta GUID
        meta_guid = meta["GUID"]
        if m_res := self._db.check_id_for_uniqueness(meta_guid):
            if m_res != "META":
                raise GUIDError(f"Meta GUID collided with GUID of type {m_res}")

        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=meta_guid, value="META")

        composer.make_META_ADDED(
            citation_guid=citation_guid,
            meta_guid=meta_guid,
            author=meta["author"],
            publisher=meta["publisher"],
            title=meta["title"],
            # unpack remaining values after filtering for the ones we already have
            **{
                k: v
                for k, v in meta.items()
                if k not in ("author", "title", "publisher", "GUID")
            },
        )

        composer.make_CITATION_ADDED(
            text=text,
            tags=tag_guids,
            meta=meta_guid,
            citation_guid=citation_guid,
            summary_guid=summary_guid,
        )

        # check summary guid
        if s_res := self._db.check_id_for_uniqueness(summary_guid):
            if s_res != "SUMMARY":
                raise GUIDError(f"Summary GUID collided with GUID of type {s_res}")
            # we're adding a new citation to this summary
            composer.make_SUMMARY_TAGGED(
                citation_guid=citation_guid, summary_guid=summary_guid
            )
        else:
            # this is a new summary
            composer.make_SUMMARY_ADDED(
                citation_guid=citation_guid,
                summary_guid=summary_guid,
                text=summary_text,
            )
            self._db.add_to_stm(key=summary_guid, value="SUMMARY")

        return composer.events

    def __parse_tags(
        self, tags, summary_guid: str, composer: EventComposer
    ) -> list[str]:
        """Validates each tag's GUID and adds it to composer according to type."""

        tag_guids = []
        for tag in tags:
            t_guid = tag["GUID"]
            t_type = tag["type"]
            if t_type not in TAG_TYPES:
                raise UnknownTagTypeError(
                    f"Tag of unknown type {t_type} was encountered"
                )

            # check if tag already exists in the database
            if t_res := self._db.check_id_for_uniqueness(t_guid):
                # and if it does, it must be the same type as this tag
                if t_type != t_res:
                    raise GUIDError(
                        f"Tag GUID of type {t_type} doesn't match database type of {t_res}."
                    )

                # make a tag of the correct type
                if t_type == "PERSON":
                    log.debug(f'Tagging person {tag["name"]} of GUID {t_guid}')
                    composer.make_PERSON_TAGGED(
                        summary_guid=summary_guid,
                        person_guid=t_guid,
                        person_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                    )
                elif t_type == "PLACE":
                    log.debug(f'Tagging place {tag["name"]} of GUID {t_guid}')
                    composer.make_PLACE_TAGGED(
                        summary_guid=summary_guid,
                        place_guid=t_guid,
                        place_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                    )
                elif t_type == "TIME":
                    log.debug(f'Tagging time {tag["name"]} of GUID {t_guid}')
                    composer.make_TIME_TAGGED(
                        summary_guid=summary_guid,
                        time_guid=t_guid,
                        time_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                    )
                else:
                    raise Exception(
                        f"Tag of unknown type {t_type} received - in tagged"
                    )

            # now we know our GUID is unique, so we need to construct a new tag
            else:

                # first add it to short term memory
                self._db.add_to_stm(key=t_guid, value=t_type)

                # make a tag of the correct type
                if t_type == "PERSON":
                    log.debug(f'Adding person {tag["name"]} of GUID {t_guid}')
                    composer.make_PERSON_ADDED(
                        summary_guid=summary_guid,
                        person_guid=t_guid,
                        person_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                    )
                elif t_type == "PLACE":
                    log.debug(f'Adding place {tag["name"]} of GUID {t_guid}')
                    composer.make_PLACE_ADDED(
                        summary_guid=summary_guid,
                        place_guid=t_guid,
                        place_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                        latitude=tag["latitude"],
                        longitude=tag["longitude"],
                    )
                elif t_type == "TIME":
                    log.debug(f'Adding time {tag["name"]} of GUID {t_guid}')
                    composer.make_TIME_ADDED(
                        summary_guid=summary_guid,
                        time_guid=t_guid,
                        time_name=tag["name"],
                        citation_start=tag["start_char"],
                        citation_end=tag["stop_char"],
                    )
                else:
                    raise Exception(f"Tag of unknown type {t_type} received - in added")

            log.debug(f"Successfully validated tag {tag}")
            tag_guids.append(t_guid)
        return tag_guids
