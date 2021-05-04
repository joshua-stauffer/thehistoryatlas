"""Component responsible for updating database to reflect incoming persisted events.

Monday, May 3rd 2021
"""

import logging
from .errors import UnknownEventError

log = logging.getLogger(__name__)

class EventHandler:

    def __init__(self, database_instance):
        self._db = database_instance
        self._event_handlers = self._map_event_handlers()

    def handle_event(self, event):
        """Process an incoming event and persist it to the database"""
        evt_type = event.get('type')
        handler = self._event_handlers.get(evt_type)
        if not handler:
            raise UnknownEventError(evt_type)
        handler(event['payload'])

    def _map_event_handlers(self):
        """A dict of known event types and the methods which process them"""
        return {
            'CITATION_ADDED': self._handle_citation_added,
            'PERSON_ADDED': self._handle_person_added,
            'PLACE_ADDED': self._handle_place_added,
            'TIME_ADDED': self._handle_time_added,
            'PERSON_TAGGED': self._handle_person_tagged,
            'PLACE_TAGGED': self._handle_place_tagged,
            'TIME_TAGGED': self._handle_time_tagged,
            'META_ADDED': self._handle_meta_added
        }

    def _handle_citation_added(self, event):
        transaction_guid = event['guid']
        citation_guid = event['payload']['guid']
        text = event['payload']['text']
        self._db.create_citation(
            transaction_guid=transaction_guid,
            citation_guid=citation_guid,
            text=text)

    def _handle_person_added(self, event):
        transaction_guid = event['guid']
        payload = event['payload']
        citation_guid = payload['citation_guid']
        person_guid = payload['person_guid']
        person_name = payload['person_name']
        start_char = payload['citation_start']
        stop_char = payload['citation_end']
        

    def _handle_person_tagged(self, event):
        pass

    def _handle_place_added(self, event):
        pass

    def _handle_place_tagged(self, event):
        pass

    def _handle_time_added(self, event):
        pass

    def _handle_time_tagged(self, event):
        pass

    def _handle_meta_added(self, event):
        pass