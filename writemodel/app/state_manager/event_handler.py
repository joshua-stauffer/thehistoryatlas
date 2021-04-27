"""Component responsible for updating the WriteModel validation database
upon receiving Persisted Events.

Friday, April 9th 2021
"""

import json
import logging
from .handler_errors import PersistedEventError, UnknownEventTypeError

log = logging.getLogger(__name__)

class EventHandler:

    def __init__(self, database_instance, hash_text):
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
            'CITATION_PUBLISHED': self._handle_citation_published
        }
        
    # event handlers
    def _handle_citation_published(self, body):
        """Receives a newly published citation and saves a hash of it in
        order to validate incoming citation texts as unique"""

        log.debug(f'Handling a new published citation {body}')
        GUID = body['payload']['GUID']
        text = body['payload']['text']
        if not GUID and text:
            logging.critical(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')
            raise PersistedEventError(f'EventHandler: malformed Persisted Event was received. GUID: {GUID} text: {text}')
        hashed_text = self._hashfunc(text)
        self._db.add_citation_hash(hashed_text, GUID)
        logging.info(f'EventHandler: successfully added new citation hash for GUID {GUID}.')
