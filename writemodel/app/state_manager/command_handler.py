"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import json

class CommandHandler:
    """Class encapsulating logic to transform Commands from the user
    into canonical Events to be passed on to the Event Store."""

    def __init__(self, database_instance, hash_text):
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
        self._hashfunc = hash_text
 
    def handle_command(self, command):
        """Receives a json command, processes it, and returns an Event
        or raises an Exception"""

        cmd = json.loads(command)
        cmd_type = cmd.get('type')

        handler = self._command_handlers.get(cmd_type)
        if not handler:
            raise ValueError(f'Unknown command {cmd_type}')
        event = handler(cmd)
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
        Raises a CommandFailed error if 
        """
        # validate that this text is unique
        text = cmd['payload']['text']
        hashed_text = self._hashfunc(text)
        if GUID := self.db.check_citation_for_uniqueness(hashed_text):
            raise CitationExistsError(GUID)
        return {
            'type': 'CITATION_PUBLISHED',
            'timestamp': cmd['timestamp'],
            'user': cmd['user'],
            'payload': cmd['payload']
        }

class CommandFailedError(Exception):
    """Base class for CommandHandler exceptions"""
    pass

class CitationExistsError(CommandFailedError):
    """Raised when attempting to add a citation that already exists in the
    database. Returns the GUID of the existing citation."""
    def __init__(self, GUID):
        self.GUID = GUID