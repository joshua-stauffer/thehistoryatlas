"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import json

class CommandHandler:

    def __init__(self, database_instance):
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
 
    def handle_command(self, command):
        """Receives a json command, processes it, and returns an Event
        or raises an Exception"""

        cmd = json.loads(command)
        cmd_type = cmd.get('type')

        handler = self._command_handlers.get(cmd_type)
        if not handler:
            raise ValueError(f'Unknown command {cmd_type}')
        event = handler(cmd)
        return eventd

    def _map_command_handlers(self):
        """Returns a dict of known commands mapping to their handle method."""
        return {
            'AddPerson': self._handle_add_person,
            'AddPersonName': self._handle_add_person_name,
        }
        
    # command handlers
    def _handle_add_person(self, cmd):
        """Handles the AddPerson command.
        
        Should succeed provided the data is of the correct type.
        """

        return {
            'type': 'PersonAdded',
            'timestamp': cmd['timestamp'],
            'user': cmd['user'],
            'payload': {
                'name': cmd['payload']['name']
            }
        }

    def _handle_add_person_name(self, cmd):
        """Handles the AddPersonName command.

        Should succeed if the name is not yet associated with that person.
        """
        raise NotImplementedError()