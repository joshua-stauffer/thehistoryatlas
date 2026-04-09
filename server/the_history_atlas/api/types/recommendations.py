from uuid import UUID

from pydantic import BaseModel


class RelatedEvent(BaseModel):
    summaryId: UUID
    summaryText: str
    sharedTags: int = 0
    similarity: float | None = None


class RelatedEventsResponse(BaseModel):
    events: list[RelatedEvent]
