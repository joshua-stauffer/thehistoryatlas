"""Component responsible for updating the WriteModel validation database
upon receiving Persisted Events.

Friday, April 9th 2021
"""

import logging
from typing import Callable, Dict

from abstract_domain_model.models import (
    CitationAdded,
    SummaryAdded,
    SummaryTagged,
    MetaAdded,
    PersonAdded,
    PlaceAdded,
    TimeAdded,
    PersonTagged,
    PlaceTagged,
    TimeTagged,
)
from abstract_domain_model.models.events.meta_tagged import MetaTagged
from abstract_domain_model.types import Event, EventTypes
from writemodel.state_manager.handler_errors import MalformedEventError
from writemodel.state_manager.handler_errors import UnknownEventTypeError
from writemodel.state_manager.handler_errors import MissingEventFieldError
from writemodel.state_manager.handler_errors import DuplicateEventError


log = logging.getLogger(__name__)

EventHandlerMethod = Callable[[Event], None]


class EventHandler:
    """Class which validates incoming events from the event.persisted stream
    and stores necessary updates to the validation database."""

    def __init__(self, database_instance, hash_text):
        """
        params:
            database_instance: class which provides database access methods
            hash_text: function which provides a stable hash on a string
        """
        self._event_handlers: Dict[
            EventTypes, EventHandlerMethod
        ] = self._map_event_handlers()
        self._db = database_instance
        self._hashfunc = hash_text
        self._event_id_set = set()

    def handle_event(self, event: Event):
        """Receives a dict, processes it, and updates
        the WriteModel database accordingly"""

        logging.info(f"EventHandler: processing event {event}")
        event_index = event.index
        if not event_index:
            raise MissingEventFieldError
        if event_index in self._event_id_set:
            log.info(
                f"Discarding malformed or duplicate message with event_id {event_index}."
            )
            raise DuplicateEventError
        handler = self._event_handlers.get(event.type)
        if not handler:
            raise UnknownEventTypeError
        handler(event)
        self._event_id_set.add(event_index)

    def _map_event_handlers(self):
        """Returns a dict of known events mapping to their handle method."""
        return {
            "CITATION_ADDED": self._handle_citation_added,
            "META_ADDED": self._handle_meta_added,
            "PERSON_ADDED": self._handle_person_added,
            "PLACE_ADDED": self._handle_place_added,
            "TIME_ADDED": self._handle_time_added,
            "PERSON_TAGGED": self._handle_person_tagged,
            "PLACE_TAGGED": self._handle_place_tagged,
            "TIME_TAGGED": self._handle_time_tagged,
            "SUMMARY_ADDED": self._handle_summary_added,
            "SUMMARY_TAGGED": self._handle_summary_tagged,
            "META_TAGGED": self._handle_meta_tagged,
        }

    # event handlers

    def _handle_citation_added(self, event: CitationAdded):
        """new citation has been entered"""

        log.debug(f"Handling a newly published citation {event}")
        citation_id = event.payload.id
        text = event.payload.text
        if not citation_id and text:
            logging.critical(
                f"EventHandler: malformed Persisted Event was received. GUID: {citation_id} text: {text}"
            )
            raise MalformedEventError(
                f"EventHandler: malformed Persisted Event was received. GUID: {citation_id} text: {text}"
            )
        if event.index is None:
            raise MissingEventFieldError
        # persist the hashed text to db
        hashed_text = self._hashfunc(text)
        self._db.add_citation_hash(hashed_text, citation_id)
        logging.info(
            f"Successfully persisted new citation hash for GUID {citation_id}."
        )

        # persist the guid
        self._db.add_guid(value=citation_id, type="CITATION")
        logging.info(
            f"Successfully persisted CITATION with GUID {citation_id} to database."
        )

        # update our record of the latest handled event
        self._db.update_last_event_id(event.index)
        self._event_id_set.add(event.index)

    def _handle_summary_added(self, event: SummaryAdded):
        """a new summary has been created"""
        self._db.add_guid(value=event.payload.id, type="SUMMARY")

    def _handle_summary_tagged(self, event: SummaryTagged):
        """An existing summary has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_meta_added(self, event: MetaAdded):
        """a metadata instance has been entered"""
        self._db.add_guid(value=event.payload.id, type="META")

    def _handle_meta_tagged(self, event: MetaTagged):
        # no op
        pass

    def _handle_person_added(self, event: PersonAdded):
        """a new person instance has been created"""
        self._db.add_guid(value=event.payload.id, type="PERSON")

    def _handle_place_added(self, event: PlaceAdded):
        """a new place instance has been created"""
        self._db.add_guid(value=event.payload.id, type="PLACE")

    def _handle_time_added(self, event: TimeAdded):
        """a new time instance has been created"""
        self._db.add_guid(value=event.payload.id, type="TIME")

    def _handle_person_tagged(self, event: PersonTagged):
        """an existing person has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_place_tagged(self, event: PlaceTagged):
        """an existing place has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_time_tagged(self, event: TimeTagged):
        """an existing time has been tagged"""
        # GUID already exists, no need to do anything
        pass
