import logging
from uuid import UUID

from text_reader.rest_client import RestClient
from text_reader.types import ResolvedEvent

log = logging.getLogger(__name__)


class Publisher:
    def __init__(self, rest_client: RestClient):
        self._rest = rest_client

    def ensure_story(self, source_id: UUID, source_title: str) -> UUID:
        """Get or create a text-reader story for the given source."""
        existing = self._rest.get_story_by_source(str(source_id))
        if existing and existing.get("id"):
            log.info(f"Using existing story: {existing['name']}")
            return UUID(existing["id"])

        story = self._rest.create_story(
            name=f"From: {source_title}",
            description=f"Events extracted from {source_title}",
            source_id=str(source_id),
        )
        log.info(f"Created new story: {story['name']}")
        return UUID(story["id"])

    def publish_event(
        self,
        event: ResolvedEvent,
        source_id: UUID,
        story_id: UUID,
    ) -> UUID | None:
        """Publish a resolved event to the server. Returns summary ID."""
        # Build tag list with char offsets
        tags = self._build_tags(event)
        if not tags:
            log.warning(f"Could not build tags for event: {event.summary[:50]}")
            return None

        # Build citation
        citation = {
            "text": event.excerpt,
            "page_num": event.page_num,
        }

        try:
            result = self._rest.create_event(
                summary=event.summary,
                tags=tags,
                citation=citation,
                source_id=str(source_id),
                story_id=str(story_id),
            )
            return UUID(result["id"])
        except Exception as e:
            log.error(f"Failed to publish event: {e}")
            return None

    def _build_tags(self, event: ResolvedEvent) -> list[dict]:
        """Build tag list with character offsets by finding entity names in the summary."""
        tags = []
        summary = event.summary

        for person in event.people:
            start = summary.find(person.name)
            if start == -1:
                log.warning(f"Person '{person.name}' not found in summary text")
                continue
            tags.append(
                {
                    "id": str(person.id),
                    "name": person.name,
                    "start_char": start,
                    "stop_char": start + len(person.name),
                }
            )

        # Place
        place_start = summary.find(event.place.name)
        if place_start == -1:
            log.warning(f"Place '{event.place.name}' not found in summary text")
            return []
        tags.append(
            {
                "id": str(event.place.id),
                "name": event.place.name,
                "start_char": place_start,
                "stop_char": place_start + len(event.place.name),
            }
        )

        # Time
        time_start = summary.find(event.time.name)
        if time_start == -1:
            log.warning(f"Time '{event.time.name}' not found in summary text")
            return []
        tags.append(
            {
                "id": str(event.time.id),
                "name": event.time.name,
                "start_char": time_start,
                "stop_char": time_start + len(event.time.name),
            }
        )

        return tags
