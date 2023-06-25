import logging

from the_history_atlas.apps.domain.transform import to_dict
from the_history_atlas.apps.eventstore.database import Database
from the_history_atlas.apps.config import Config

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class EventStore:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)

    async def process_event(self, event, pub_func):
        """accepts an event and submits it to the datastore for storage.
        Returns a json string representation of the persisted event."""
        log.debug(f"processing event {event}")
        persisted_events = self.db.commit_event(event)
        for event in persisted_events:
            await pub_func(to_dict(event))
        log.info("Finished processing event")
