from the_history_atlas.apps.database.database_app import DatabaseClient
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.writemodel.state_manager.database import Database
from the_history_atlas.apps.writemodel.state_manager.command_handler import (
    CommandHandler,
)
from the_history_atlas.apps.writemodel.state_manager.event_handler import EventHandler
from the_history_atlas.apps.writemodel.state_manager.text_processor import TextHasher


class Manager:
    """A class to share the database resource between command handlers
    and event handlers."""

    def __init__(self, config: Config, database_client: DatabaseClient):
        self.db = Database(database_client=database_client)
        self.hasher = TextHasher()
        self.command_handler = CommandHandler(self.db, self.hasher.get_hash)
        self.event_handler = EventHandler(self.db, self.hasher.get_hash)
