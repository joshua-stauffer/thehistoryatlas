import logging
from copy import deepcopy
from typing import Union, Dict, List
from uuid import uuid4

from the_history_atlas.apps.domain.models import (
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
from the_history_atlas.apps.domain.models.commands.publish_citation import (
    PublishCitation,
    Time,
    Place,
    Person,
)
from the_history_atlas.apps.domain.models.events.meta_tagged import (
    MetaTagged,
    MetaTaggedPayload,
)
from the_history_atlas.apps.domain.types import Command, Event, PublishCitationType
from the_history_atlas.apps.writemodel.state_manager.handler_errors import (
    CitationExistsError,
    NoValidatorError,
    MissingResourceError,
)
from the_history_atlas.apps.writemodel.state_manager.handler_errors import GUIDError
from the_history_atlas.apps.writemodel.state_manager.handler_errors import (
    UnknownTagTypeError,
)

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
        handler = self._command_handlers[type(command)]
        events = handler(command)
        return events

    def validate_command(self, command: Command) -> bool:
        validate = self._command_validators.get(type(command), None)
        if validate is None:
            raise NoValidatorError
        return validate(command)

    def _map_command_handlers(self) -> Dict[type, callable]:
        """Returns a dict of known commands mapping to their handle method."""
        return {
            PublishCitationType: self.transform_publish_citation_to_events,
        }

    def _map_command_validators(self) -> Dict[type, callable]:
        """Returns a dict of known commands mapping to their validator method."""
        return {
            PublishCitationType: self.validate_publish_citation,
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
