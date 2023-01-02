"""Component responsible for updating database to reflect incoming persisted events.

Monday, May 3rd 2021
"""

import logging
from dataclasses import asdict
from typing import Union

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
            "PERSON_TAGGED": self._handle_person_tagged,
            "PLACE_TAGGED": self._handle_place_tagged,
            "TIME_TAGGED": self._handle_time_tagged,
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
            citation_guid=citation_guid, summary_guid=summary_guid, text=text
        )

    def _handle_person_added(self, event: PersonAdded):
        self.__handle_person_util(event=event, is_new=True)

    def _handle_person_tagged(self, event: PersonTagged):
        self.__handle_person_util(event=event, is_new=False)

    def __handle_person_util(self, event: Union[PersonTagged, PersonAdded], is_new):
        """Merges person added and person tagged functionality"""
        self._db.handle_person_update(
            person_guid=event.payload.id,
            summary_guid=event.payload.summary_id,
            person_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            is_new=is_new,
        )

    def _handle_place_added(self, event: PlaceAdded):
        latitude = event.payload.latitude
        longitude = event.payload.longitude
        geo_shape = event.payload.geo_shape
        self.__handle_place_util(
            event=event,
            is_new=True,
            latitude=latitude,
            longitude=longitude,
            geoshape=geo_shape,
        )

    def _handle_place_tagged(self, event: PlaceTagged):
        self.__handle_place_util(event=event, is_new=False)

    def __handle_place_util(
        self, event: Union[PlaceAdded, PlaceTagged], is_new, **kwargs
    ):
        """Merges place added and place tagged functionality"""
        # latitude, longitude, and geoshape are passed through as keyword
        # arguments since they are only needed by place added
        self._db.handle_place_update(
            place_guid=event.payload.id,
            summary_guid=event.payload.summary_id,
            place_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            is_new=is_new,
            **kwargs,
        )

    def _handle_time_added(self, event: TimeAdded):
        self.__handle_time_util(event=event, is_new=True)

    def _handle_time_tagged(self, event: TimeTagged):
        self.__handle_time_util(event=event, is_new=False)

    def __handle_time_util(self, event: Union[TimeAdded, TimeTagged], is_new):
        """Merges time added and time tagged functionality"""
        self._db.handle_time_update(
            time_guid=event.payload.id,
            summary_guid=event.payload.summary_id,
            time_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            is_new=is_new,
        )

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
