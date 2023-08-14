import logging
from typing import List, Callable

from sqlalchemy.engine import Engine

from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.eventstore.database import Database
from the_history_atlas.apps.config import Config

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


SubscriberCallback = Callable[[Event], None]


class EventStore:
    def __init__(self, config: Config, database_client: Engine):
        self._config = config
        self._db = Database(engine=database_client)
        self._subscribers: List[SubscriberCallback] = []

    def publish_events(self, events: List[Event]) -> None:
        log.debug(f"processing event {events}")
        persisted_events = self._db.commit_events(events)
        for event in persisted_events:
            self._publish_to_subscribers(event)
        log.info("Finished processing event")

    def subscribe(self, callback: SubscriberCallback) -> None:
        self._subscribers.append(callback)

    def _publish_to_subscribers(self, event: Event) -> None:
        for callback in self._subscribers:
            callback(event)
