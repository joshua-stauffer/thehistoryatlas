"""Component responsible for updating the WriteModel validation database
upon receiving Persisted Events.

Friday, April 9th 2021
"""

import logging
from .handler_errors import MalformedEventError
from .handler_errors import UnknownEventTypeError
from .handler_errors import MissingEventFieldError
from .handler_errors import DuplicateEventError


log = logging.getLogger(__name__)

class EventHandler:
    """Class which validates incoming events from the event.persisted stream
    and stores necessary updates to the validation database."""

    def __init__(self, database_instance, hash_text):
        """
        params:
            database_instance: class which provides database access methods
            hash_text: function which provides a stable hash on a string
        """
        self._event_handlers = self._map_event_handlers()
        self._db = database_instance
        self._hashfunc = hash_text
        self._event_id_set = set()

    def handle_event(self, event):
        """Receives a dict, processes it, and updates
        the WriteModel database accordingly"""

        logging.info(f'EventHandler: processing event {event}')
        event_id = event.get('event_id')
        if not event_id:
            raise MissingEventFieldError
        if event_id in self._event_id_set:
            log.info(f'Discarding malformed or duplicate message with event_id {event_id}.')
            raise DuplicateEventError
        evt_type = event.get('type')
        handler = self._event_handlers.get(evt_type)
        if not handler:
            raise UnknownEventTypeError
        handler(event)
        self._event_id_set.add(event_id)

    def _map_event_handlers(self):
        """Returns a dict of known events mapping to their handle method."""
        return {
            'CITATION_ADDED':   self._handle_citation_added,
            'META_ADDED':       self._handle_meta_added,
            'PERSON_ADDED':     self._handle_person_added,
            'PLACE_ADDED':      self._handle_place_added,
            'TIME_ADDED':       self._handle_time_added,
            'PERSON_TAGGED':    self._handle_person_tagged,
            'PLACE_TAGGED':     self._handle_place_tagged,
            'TIME_TAGGED':      self._handle_time_tagged,
            'SUMMARY_ADDED':    self._handle_summary_added,
            'SUMMARY_TAGGED':   self._handle_summary_tagged
        }
        
    # event handlers

    def _handle_citation_added(self, event):
        """new citation has been entered"""

        log.debug(f'Handling a newly published citation {event}')
        GUID = event['payload']['citation_guid']
        text = event['payload']['text']
        if not GUID and text:
            logging.critical(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')
            raise MalformedEventError(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')
        event_id = event.get('event_id')
        if not event_id:
            raise MissingEventFieldError
        # persist the hashed text to db
        hashed_text = self._hashfunc(text)
        self._db.add_citation_hash(hashed_text, GUID)
        logging.info(f'Successfully persisted new citation hash for GUID {GUID}.')

        # persist the guid
        self._db.add_guid(value=GUID, type='CITATION')
        logging.info(f'Successfully persisted CITATION with GUID {GUID} to database.')

        # update our record of the latest handled event
        self._db.update_last_event_id(event['event_id'])
        self._event_id_set.add(event_id)

    def _handle_summary_added(self, body):
        """a new summary has been created"""
        GUID = body['payload']['summary_guid']
        self._db.add_guid(value=GUID, type='SUMMARY')

    def _handle_summary_tagged(self, body):
        """An existing summary has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_meta_added(self, body):
        """a metadata instance has been entered"""

        GUID = body['payload']['meta_guid']
        self._db.add_guid(value=GUID, type='META')

    def _handle_person_added(self, body):   
        """a new person instance has been created"""

        GUID = body['payload']['person_guid']
        self._db.add_guid(value=GUID, type='PERSON')

    def _handle_place_added(self, body):
        """a new place instance has been created"""

        GUID = body['payload']['place_guid']
        self._db.add_guid(value=GUID, type='PLACE')

    def _handle_time_added(self, body):
        """a new time instance has been created"""

        GUID = body['payload']['time_guid']
        self._db.add_guid(value=GUID, type='TIME')

    def _handle_person_tagged(self, body):
        """an existing person has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_place_tagged(self, body):
        """an existing place has been tagged"""
        # GUID already exists, no need to do anything
        pass

    def _handle_time_tagged(self, body):
        """an existing time has been tagged"""
        # GUID already exists, no need to do anything
        pass
