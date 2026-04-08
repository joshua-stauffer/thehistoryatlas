"""Base class for event factories."""

from abc import ABC, abstractmethod
from typing import List, Type, Dict, Any, Optional
import time
import logging

from wiki_service.types import Entity, Query
from wiki_service.types import WikiEvent
from wiki_service.tracing import trace_time

logger = logging.getLogger(__name__)


class UnprocessableEventError(Exception):
    """Raised when an event cannot be processed."""

    pass


class EventFactory(ABC):
    """Base class for event factories."""

    def __init__(self, entity: Entity, query: Query, entity_type: str):
        self._entity = entity
        self._query = query
        self._entity_type = entity_type
        self._entity_id = entity.id  # Store the entity ID for use in WikiEvent creation
        self._processing_time = 0.0  # Track processing time
        self._events_created = 0  # Track number of events created

    @property
    @abstractmethod
    def version(self) -> int:
        """Get the version of the event factory."""
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        """Get the label of the event factory."""
        pass

    @property
    def after_labels(self) -> list[str]:
        """Represent logical relationships between types of events, in the
        case that they share a date."""
        return []

    @abstractmethod
    def entity_has_event(self) -> bool:
        """Check if the entity has this type of event."""
        pass

    @trace_time()
    def create_wiki_event(self) -> List[WikiEvent]:
        """Create a wiki event from the entity."""
        start_time = time.time()
        try:
            events = self._create_events()
            self._events_created = len(events)
            return events
        finally:
            self._processing_time = (time.time() - start_time) * 1000  # ms

    @abstractmethod
    def _create_events(self) -> List[WikiEvent]:
        """Internal method to create events, to be implemented by subclasses."""
        pass

    def _create_base_context(self) -> Dict[str, Any]:
        """Create base context dictionary with entity information."""
        context = {
            "entity_type": self._entity_type,
            "entity_id": self._entity_id,
            "entity_labels": self._entity.labels.get("en"),
            "entity_descriptions": self._entity.descriptions.get("en"),
        }
        return context

    @property
    def processing_time(self) -> float:
        """Get the processing time in milliseconds."""
        return self._processing_time

    @property
    def events_created_count(self) -> int:
        """Get the number of events created."""
        return self._events_created


_event_factories: List[Type[EventFactory]] = []


def register_event_factory(cls: Type[EventFactory]) -> Type[EventFactory]:
    """Register an event factory."""
    _event_factories.append(cls)
    return cls


def get_event_factories(
    entity: Entity, query: Query, entity_type: str
) -> List[EventFactory]:
    """Get all registered event factories."""
    return [
        factory_class(entity=entity, query=query, entity_type=entity_type)
        for factory_class in _event_factories
    ]
