"""Component responsible for updating database to reflect incoming persisted events.

Monday, May 3rd 2021
"""

import logging
from dataclasses import asdict
from typing import Union, List

from abstract_domain_model.models import (
    SummaryAdded,
    SummaryTagged,
    CitationAdded,
    PersonAdded,
    PersonTagged,
    PlaceAdded,
    PlaceTagged,
    TimeAdded,
    TimeTagged,
    MetaAdded,
)
from abstract_domain_model.models.core import Name
from abstract_domain_model.models.events.meta_tagged import MetaTagged
from abstract_domain_model.transform import from_dict
from abstract_domain_model.types import Event
from readmodel.errors import (
    UnknownEventError,
    MissingEventFieldError,
    DuplicateEventError,
)

log = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, database_instance):
        self._db = database_instance
        self._event_handlers = self._map_event_handlers()
        # using this for now, may need to transition to a different solution
        # if the database gets really large in production
        self._event_id_set = set()

    def handle_event(self, event: Event):
        """Process an incoming event and persist it to the database"""

        if event.index in self._event_id_set:
            log.info(
                f"Discarding malformed or duplicate message with event_id {event.index}."
            )
            raise DuplicateEventError

        handler = self._event_handlers.get(event.type)
        if not handler:
            raise UnknownEventError(event.type)
        handler(event)
        # update our record of the latest handled event
        self._db.update_last_event_id(event.index)
        self._event_id_set.add(event.index)

    def _map_event_handlers(self):
        """A dict of known event types and the methods which process them"""
        return {
            "SUMMARY_ADDED": self._handle_summary_added,
            "SUMMARY_TAGGED": self._handle_summary_tagged,
            "CITATION_ADDED": self._handle_citation_added,
            "PERSON_ADDED": self._handle_person_added,
            "PLACE_ADDED": self._handle_place_added,
            "TIME_ADDED": self._handle_time_added,
            "PERSON_TAGGED": self._handle_entity_tagged,
            "PLACE_TAGGED": self._handle_entity_tagged,
            "TIME_TAGGED": self._handle_entity_tagged,
            "META_ADDED": self._handle_meta_added,
            "META_TAGGED": self._handle_meta_tagged,
        }

    def _handle_summary_added(self, event: SummaryAdded):
        summary_guid = event.payload.id
        text = event.payload.text
        self._db.create_summary(summary_guid=summary_guid, text=text)

    def _handle_summary_tagged(self, event: SummaryTagged):
        # summary will automatically be tagged when the
        # new citation is added.
        pass

    def _handle_citation_added(self, event: CitationAdded):
        citation_guid = event.payload.id
        summary_guid = event.payload.summary_id
        text = event.payload.text
        self._db.create_citation(
            citation_guid=citation_guid,
            summary_guid=summary_guid,
            text=text,
            access_date=event.payload.access_date,
            page_num=event.payload.page_num,
        )

    def _handle_person_added(self, event: PersonAdded):
        self._db.create_person(self, event=event)

    def _handle_entity_tagged(
        self, event: Union[PersonTagged, PlaceTagged, TimeTagged]
    ):
        self._db.tag_entity(
            id=event.payload.id,
            summary_id=event.payload.summary_id,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
        )

    def _handle_place_added(self, event: PlaceAdded):
        self._db.create_place(event)

    def _handle_time_added(self, event: TimeAdded):
        self._db.create_place(event)

    def _handle_meta_added(self, event: MetaAdded):
        source = event.payload
        self._db.create_source(
            id=source.id,
            title=source.title,
            author=source.author,
            publisher=source.publisher,
            pub_date=source.pub_date,
            citation_id=source.citation_id,
        )

    def _handle_meta_tagged(self, event: MetaTagged):
        self._db.add_source_to_citation(
            source_id=event.payload.id, citation_id=event.payload.citation_id
        )
