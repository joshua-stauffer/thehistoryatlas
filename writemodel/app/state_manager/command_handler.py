"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import json
import logging
from .handler_errors import CitationExistsError, UnknownCommandTypeError

class CommandHandler:
    """Class encapsulating logic to transform Commands from the user
    into canonical Events to be passed on to the Event Store."""

    def __init__(self, database_instance, hash_text):
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
        self._hashfunc = hash_text
 
    def handle_command(self, command: dict):
        """Receives a dict, processes it, and returns an Event
        or raises an Exception"""

        cmd_type = command.get('type')
        handler = self._command_handlers.get(cmd_type)
        if not handler:
            raise UnknownCommandTypeError
        event = handler(command)
        return event

    def _map_command_handlers(self):
        """Returns a dict of known commands mapping to their handle method."""
        return {
            'PUBLISH_NEW_CITATION': self._handle_publish_new_citation,
        }
        
    # command handlers
    def _handle_publish_new_citation(self, cmd):
        """Handles the PUBLISH_NEW_CITATION command.
        Raises a KeyError if a field of the command is not present.
        Raises a CommandFailed error if text is not unique.
        """
        
        logging.info(f'CommandHandler: received a new citation: {cmd}')
        # validate that this text is unique
        text = cmd['payload']['text']
        hashed_text = self._hashfunc(text)
        logging.debug(f'Text hash is {hashed_text}')
        if result := self._db.check_citation_for_uniqueness(hashed_text):
            logging.info('CommandHandler: tried (and failed) to publish duplicate citation')
            raise CitationExistsError(result.GUID)
        logging.debug('CommandHandler: successfully validated new citation')
        return {
            'type': 'CITATION_PUBLISHED',
            'timestamp': cmd['timestamp'],
            'user': cmd['user'],
            'payload': cmd['payload']
        }
