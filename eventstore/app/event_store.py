"""
Primary class of the EventStore component. Supports writing to the
canonical database for the History Atlas.
"""

import json
import os
from database import Database
from broker import Broker
from config import Config

class EventStore:

    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.broker = Broker(self.config, self.add_event)

    def add_event(self, event):
        """accepts an event and submits it to the datastore for storage.
        Returns a json string representation of the persisted event."""

        e = json.loads(event.decode())
        persisted_event = self.db.commit_event(e)
        return persisted_event


if __name__ == "__main__":
    store = EventStore()
    store.broker.listen()
