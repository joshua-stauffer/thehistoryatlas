"""Component responsible for updating database to reflect incoming persisted events.

Monday, May 3rd 2021
"""

import logging
from app.errors import UnknownEventError, MissingEventFieldError, DuplicateEventError

log = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, database_instance):
        self._db = database_instance
        self._event_handlers = self._map_event_handlers()
        # using this for now, may need to transition to a different solution
        # if the database gets really large in production
        self._event_id_set = set()

    def handle_event(self, event):
        """Process an incoming event and persist it to the database"""
        evt_type = event.get("type")
        event_id = event.get("event_id")
        if not event_id:
            raise MissingEventFieldError
        if event_id in self._event_id_set:
            log.info(
                f"Discarding malformed or duplicate message with event_id {event_id}."
            )
            raise DuplicateEventError
        handler = self._event_handlers.get(evt_type)
        if not handler:
            raise UnknownEventError(evt_type)
        handler(event)
        # update our record of the latest handled event
        self._db.update_last_event_id(event_id)
        self._event_id_set.add(event_id)

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
        }

    def _handle_summary_added(self, event):
        summary_guid = event["payload"]["summary_guid"]
        text = event["payload"]["text"]
        self._db.create_summary(summary_guid=summary_guid, text=text)

    def _handle_summary_tagged(self, event):
        # summary will automatically be tagged when the
        # new citation is added.
        pass

    def _handle_citation_added(self, event):
        citation_guid = event["payload"]["citation_guid"]
        summary_guid = event["payload"]["summary_guid"]
        text = event["payload"]["text"]
        self._db.create_citation(
            citation_guid=citation_guid, summary_guid=summary_guid, text=text
        )

    def _handle_person_added(self, event):
        self.__handle_person_util(event=event, is_new=True)

    def _handle_person_tagged(self, event):
        self.__handle_person_util(event=event, is_new=False)

    def __handle_person_util(self, event, is_new):
        """Merges person added and person tagged functionality"""
        payload = event["payload"]
        self._db.handle_person_update(
            person_guid=payload["person_guid"],
            summary_guid=payload["summary_guid"],
            person_name=payload["person_name"],
            start_char=payload["citation_start"],
            stop_char=payload["citation_end"],
            is_new=is_new,
        )

    def _handle_place_added(self, event):
        payload = event["payload"]
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")
        geoshape = payload.get("geoshape")
        self.__handle_place_util(
            event=event,
            is_new=True,
            latitude=latitude,
            longitude=longitude,
            geoshape=geoshape,
        )

    def _handle_place_tagged(self, event):
        self.__handle_place_util(event=event, is_new=False)

    def __handle_place_util(self, event, is_new, **kwargs):
        """Merges place added and place tagged functionality"""
        # latitude, longitude, and geoshape are passed through as keyword
        # arguments since they are only needed by place added
        payload = event["payload"]
        self._db.handle_place_update(
            place_guid=payload["place_guid"],
            summary_guid=payload["summary_guid"],
            place_name=payload["place_name"],
            start_char=payload["citation_start"],
            stop_char=payload["citation_end"],
            is_new=is_new,
            **kwargs,
        )

    def _handle_time_added(self, event):
        self.__handle_time_util(event=event, is_new=True)

    def _handle_time_tagged(self, event):
        self.__handle_time_util(event=event, is_new=False)

    def __handle_time_util(self, event, is_new):
        """Merges time added and time tagged functionality"""
        payload = event["payload"]
        self._db.handle_time_update(
            time_guid=payload["time_guid"],
            summary_guid=payload["summary_guid"],
            time_name=payload["time_name"],
            start_char=payload["citation_start"],
            stop_char=payload["citation_end"],
            is_new=is_new,
        )

    def _handle_meta_added(self, event):
        citation_guid = event["payload"]["citation_guid"]

        # we're passing arbitrary kwargs straight through,
        # so delete the ones we don't need for the end user
        meta_payload = dict(**event["payload"])
        del meta_payload["citation_guid"]
        del meta_payload["meta_guid"]
        self._db.add_meta_to_citation(citation_guid=citation_guid, **meta_payload)
