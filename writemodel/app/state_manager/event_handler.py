"""Component responsible for updating the WriteModel validation database
upon receiving Persisted Events.

Friday, April 9th 2021
"""

import json
import logging
from .handler_errors import MalformedEventError, UnknownEventTypeError

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

    def handle_event(self, event):
        """Receives a dict, processes it, and updates
        the WriteModel database accordingly"""

        logging.info(f'EventHandler: processing event {event}')
        evt_type = event.get('type')
        handler = self._event_handlers.get(evt_type)
        if not handler:
            raise UnknownEventTypeError
        handler(event)

    def _map_event_handlers(self):
        """Returns a dict of known events mapping to their handle method."""
        return {
            'CITATION_ADDED': self._handle_citation_added,
            'META_ADDED': self._handle_meta_added,
            'PERSON_ADDED': self._handle_person_added,
            'PLACE_ADDED': self._handle_place_added,
            'TIME_ADDED': self._handle_time_added,
            'PERSON_TAGGED': self._handle_person_tagged,
            'PLACE_TAGGED': self._handle_place_added,
            'TIME_TAGGED': self._handle_time_tagged,
        }
        
    # event handlers

    def _handle_citation_added(self, body):
        """new citation has been entered"""

        log.debug(f'Handling a newly published citation {body}')
        GUID = body['payload']['GUID']
        text = body['payload']['text']
        if not GUID and text:
            logging.critical(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')
            raise MalformedEventError(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')

        # persist the hashed text to db
        hashed_text = self._hashfunc(text)
        self._db.add_citation_hash(hashed_text, GUID)
        logging.info(f'Successfully persisted new citation hash for GUID {GUID}.')

        # persist the guid
        self._db.add_guid('CITATION', GUID)
        logging.info(f'Successfully persisted CITATION with GUID {GUID} to database.')


    def _handle_meta_added(self, body):
        """a metadata instance has been entered"""

        self.__add_guid('META', body)

    def _handle_person_added(self, body):
        """a new person instance has been created"""

        self.__add_guid('PERSON', body)

    def _handle_place_added(self, body):
        """a new place instance has been created"""

        self.__add_guid('PLACE', body)

    def _handle_time_added(self, body):
        """a new time instance has been created"""

        self.__add_guid('TIME', body)

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

    # utility handlers

    def __add_guid(self, type, body):
        """utility method to persist a GUID to the database."""

        log.debug(f'Handling a newly published {type} {body}')
        GUID = body['payload']['GUID']
        if not GUID:
            logging.critical('Malformed persisted event received: no GUID')
            raise MalformedEventError('No GUID was found')
        self._db.add_guid(type, GUID)
        log.info(f'Successfully persisted {type} with GUID {GUID} to database.')
