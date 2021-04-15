"""A manager class to hold the validator database and make it available to 
the command handler and event handler classes.

Friday, April 9th 2021
"""

from .database import Database
from .command_handler import CommandHandler
from .event_handler import EventHandler

class Manager:
    """A class to share the database resource between command handlers
    and event handlers."""

    def __init__(self, config):
        self.db = Database(config)
        self.command_handler = CommandHandler(self.db)
        self.event_handler = EventHandler(self.db)
