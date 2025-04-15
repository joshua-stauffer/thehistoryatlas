"""Event factory metrics collection and reporting."""

import logging
import time
from typing import Dict, List, Any

from wiki_service.event_factories.event_factory import EventFactory

# Configure logger with a more detailed format
logger = logging.getLogger("wiki_link.tracing")
logger.setLevel(logging.INFO)

# Add console handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class EventMetrics:
    """Collect and report metrics for event factory processing."""

    def __init__(self):
        self.reset()
        logger.info("EventMetrics initialized")

    def reset(self) -> None:
        """Reset all collected metrics."""
        self.entity_start_time = time.time()
        self.total_events_created = 0
        self.factory_metrics: Dict[str, Dict[str, Any]] = {}
        logger.debug("EventMetrics reset")

    def start_entity(self) -> None:
        """Start tracking metrics for a new entity."""
        self.reset()
        logger.debug("Started tracking new entity")

    def process_factory(self, event_factory: EventFactory) -> None:
        """
        Process metrics from an event factory after it has been run.

        Args:
            event_factory: The factory that has been processed
        """
        factory_name = event_factory.label
        if factory_name not in self.factory_metrics:
            self.factory_metrics[factory_name] = {
                "count": 0,
                "events_created": 0,
                "total_time_ms": 0,
            }

        self.factory_metrics[factory_name]["count"] += 1
        self.factory_metrics[factory_name][
            "events_created"
        ] += event_factory.events_created_count
        self.factory_metrics[factory_name][
            "total_time_ms"
        ] += event_factory.processing_time
        self.total_events_created += event_factory.events_created_count

        logger.debug(
            f"Processed factory {factory_name}: "
            f"events={event_factory.events_created_count}, "
            f"time={event_factory.processing_time:.2f}ms"
        )

    def get_entity_processing_time(self) -> float:
        """Get the total processing time for the current entity in milliseconds."""
        return (time.time() - self.entity_start_time) * 1000

    def log_entity_metrics(
        self, entity_id: str, entity_name: str, entity_type: str
    ) -> None:
        """
        Log metrics about the processed entity.

        Args:
            entity_id: The ID of the processed entity
            entity_name: The name of the processed entity
            entity_type: The type of the processed entity
        """
        entity_processing_time = self.get_entity_processing_time()

        logger.info(
            f"Entity processed: {entity_id} ({entity_name}), "
            f"Type: {entity_type}, "
            f"Time: {entity_processing_time:.2f}ms, "
            f"Events created: {self.total_events_created}"
        )

        # Log factory metrics
        for factory_name, metrics in self.factory_metrics.items():
            if metrics["count"] > 0:
                avg_time = metrics["total_time_ms"] / metrics["count"]
                logger.info(
                    f"Factory: {factory_name}, "
                    f"Count: {metrics['count']}, "
                    f"Events: {metrics['events_created']}, "
                    f"Avg time: {avg_time:.2f}ms"
                )

        return entity_processing_time
