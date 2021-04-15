"""
Primary class of the History component.

Provides read-only access to the canonical Event database,
for rebuilding or replaying history.
"""

import json
import os
from database import Database
from broker import Broker
from config import Config

class HistoryPlayer:

    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.broker = Broker(self.config, self.handle_request)

    def handle_request(self, request: bin, send_func):
        """callback method for pika client. 
        
        Parses request for parameters then passes events to
        send_func one at a time. (and along the way loads the
        entire database into memory..)
        """

        priority_sort, last_event_id = self._parse_msg(request)
        events = self._get_events(priority_sort, last_event_id)

        for event in events:
            send_func(event)



    def _get_events(self, priority_sort: bool=False, last_event_id: int=0):
        """Returns an iterable of events from the canonical Event database.
        
        params
            priority_sort: flag to select sort method. Default (False) sorts
                in strictly chronological order. True sorts first based on 
                priority, which allows annulling events to be processed first,
                then sorts on chronology.
            last_event_id: optionally provides a way to begin the database
                replay at an arbitrary starting point. Not providing this
                parameter will replay the entire history. 
        """

        if priority_sort:
            return self.db.get_events_in_priority_order(last_event_id)
        else:
            return self.db.get_events_in_chron_order(last_event_id)

    def _parse_msg(self, msg: bin):
        """Utility function to get correct values from request.
        
        Expects the following values in the message (and provides
        default values in case they aren't there):
            PRIORITY_SORT: bool
            LAST_EVENT_ID: int

        Returns (priority_sort, last_event_id)
        """

        params = json.loads(msg.decode())
        
        # first get priority sort val
        #TODO: fix this to account for non True python values (i.e. typescript bools)
        priority_sort = params.get('PRIORITY_SORT', '')
        if priority_sort:
            priority_sort = True
        else:
            priority_sort = False

        # figure out the event id, if any
        last_event_id = params.get('LAST_EVENT_ID', 0)
        if last_event_id:
            try:
                last_event_id = int(last_event_id)
            except ValueError:
                last_event_id = 0

        return priority_sort, last_event_id


if __name__ == "__main__":
    store = HistoryPlayer()
    store.broker.listen()
