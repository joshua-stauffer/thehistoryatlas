"""Manager class to coordinate database access between the Command Handler 
and the Event Handler.

May 3rd, 2021
"""

from .database import Database
from .event_handler import EventHandler
from .query_handler import QueryHandler


class Manager:
    """A class to share the database resource between query handlers
    and event handlers."""

    def __init__(self, config):
        self.db = Database(config)
        self.event_handler = EventHandler(self.db)
        self.query_handler = QueryHandler(self.db)
