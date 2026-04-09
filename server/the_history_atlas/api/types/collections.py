from uuid import UUID

from pydantic import BaseModel


class CreateCollectionRequest(BaseModel):
    name: str
    description: str | None = None


class UpdateCollectionRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None


class CollectionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    visibility: str
    itemCount: int = 0


class CollectionListResponse(BaseModel):
    collections: list[CollectionResponse]


class CollectionItemResponse(BaseModel):
    summaryId: UUID
    summaryText: str
    position: int


class CollectionDetailResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    visibility: str
    items: list[CollectionItemResponse]


class AddItemRequest(BaseModel):
    summaryId: UUID
