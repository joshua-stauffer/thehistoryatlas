"""Base class for event factories."""

from abc import ABC, abstractmethod
from typing import List, Type


from wiki_service.types import Entity, Query
from wiki_service.types import WikiEvent


class UnprocessableEventError(Exception):
    """Raised when an event cannot be processed."""

    pass


class EventFactory(ABC):
    """Base class for event factories."""

    def __init__(self, entity: Entity, query: Query, entity_type: str):
        self._entity = entity
        self._query = query
        self._entity_type = entity_type

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

    @abstractmethod
    def entity_has_event(self) -> bool:
        """Check if the entity has this type of event."""
        pass

    @abstractmethod
    def create_wiki_event(self) -> List[WikiEvent]:
        """Create a wiki event from the entity."""
        pass


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
