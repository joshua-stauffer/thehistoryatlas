"""Component responsible for updating the WriteModel validation database
upon receiving Persisted Events.

Friday, April 9th 2021
"""

import json

class EventHandler:

    def __init__(self, database_instance):
        self._event_handlers = self._map_event_handlers()
        self._db = database_instance

    def handle_event(self, event):
        """Receives a json string event, processes it, and updates
        the WriteModel database accordingly"""

        evt = json.loads(event)
        evt_type = evt.get('type')

        handler = self._event_handlers.get(evt_type)
        if not handler:
            raise ValueError(f'Unknown event {evt_type}')
        handler(evt)


    def _map_event_handlers(self):
        """Returns a dict of known events mapping to their handle method."""
        return {
            'PersonAdded': self._handle_person_added,
            'PersonNameAdded': self._handle_person_name_added,
        }
        
    # event handlers
    def _handle_person_added(self, evt):
        """Handles the PersonAdded event.
        
        Should succeed provided the data is present.
        """

        name = evt['payload']['name']
        guid = evt['payload']['guid']
        if not name and guid:
            raise ValueError()

        self._db.add_person(name, guid)


    def _handle_person_name_added(self, evt):
        """Handles the PersonNameAdded event.

        Should succeed if the name is not yet associated with that person.
        """

        name = evt['payload']['name']
        guid = evt['payload']['guid']
        if not name and guid:
            raise ValueError()

        self._db.add_name_to_person(name, guid)
