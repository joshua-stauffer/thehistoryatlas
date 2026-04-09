import logging
from datetime import datetime, timezone
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
            name=f"{source_title}",
            description=f"Events from the source {source_title}",
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
            "access_date": datetime.now(timezone.utc).isoformat(),
        }

        canonical_id = (
            str(event.existing_summary_id) if event.existing_summary_id else None
        )

        try:
            result = self._rest.create_event(
                summary=event.summary,
                tags=tags,
                citation=citation,
                source_id=str(source_id),
                story_id=str(story_id),
                canonical_summary_id=canonical_id,
                theme_slugs=event.themes,
            )
            return UUID(result["id"])
        except Exception as e:
            log.error(f"Failed to publish event: {e}")
            return None

    def _build_tags(self, event: ResolvedEvent) -> list[dict]:
        """Build tag list with character offsets by finding entity names in the summary."""
        tags = []
        summary = event.summary
        claimed: list[tuple[int, int]] = []  # (start, stop) of already-tagged spans

        def find_unclaimed(search_text: str) -> int:
            """Return the first occurrence of search_text not inside a claimed range."""
            search_from = 0
            while True:
                pos = summary.find(search_text, search_from)
                if pos == -1:
                    return -1
                if not any(start <= pos < stop for start, stop in claimed):
                    return pos
                search_from = pos + 1

        for person in event.people:
            # Use summary_name (extracted form) for char offset, not canonical DB name
            person_text = person.summary_name
            start = find_unclaimed(person_text)
            if start == -1:
                log.warning(f"Person '{person_text}' not found in summary text")
                continue
            stop = start + len(person_text)
            claimed.append((start, stop))
            tags.append(
                {
                    "id": str(person.id),
                    "name": person_text,
                    "start_char": start,
                    "stop_char": stop,
                }
            )

        # Place — use summary_name (natural form) for char offset, not canonical DB name
        place_text = event.place.summary_name
        place_start = find_unclaimed(place_text)
        if place_start == -1:
            log.warning(f"Place '{place_text}' not found in summary text")
            return []
        claimed.append((place_start, place_start + len(place_text)))
        tags.append(
            {
                "id": str(event.place.id),
                "name": place_text,
                "start_char": place_start,
                "stop_char": place_start + len(place_text),
            }
        )

        # Time
        time_start = find_unclaimed(event.time.name)
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
