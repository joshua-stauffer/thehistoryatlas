from uuid import UUID

from fastapi import HTTPException

from the_history_atlas.api.types.collections import (
    CreateCollectionRequest,
    UpdateCollectionRequest,
    CollectionResponse,
    CollectionListResponse,
    CollectionDetailResponse,
    CollectionItemResponse,
    AddItemRequest,
)
from the_history_atlas.apps.app_manager import AppManager


def create_collection_handler(
    request: CreateCollectionRequest, user_id: str, apps: AppManager
) -> CollectionResponse:
    result = apps.history_app.create_collection(
        user_id=user_id, name=request.name, description=request.description
    )
    return CollectionResponse(
        id=result["id"],
        name=result["name"],
        description=result["description"],
        visibility=result["visibility"],
    )


def list_collections_handler(
    user_id: str, apps: AppManager
) -> CollectionListResponse:
    collections = apps.history_app.get_collections(user_id=user_id)
    return CollectionListResponse(
        collections=[
            CollectionResponse(
                id=c["id"],
                name=c["name"],
                description=c["description"],
                visibility=c["visibility"],
                itemCount=c["item_count"],
            )
            for c in collections
        ]
    )


def get_collection_handler(
    collection_id: UUID, user_id: str | None, apps: AppManager
) -> CollectionDetailResponse:
    collection = apps.history_app.get_collection(collection_id=collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    # Private collections only visible to owner
    if collection["visibility"] == "private" and collection["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Collection not found")
    items = apps.history_app.get_collection_items(collection_id=collection_id)
    return CollectionDetailResponse(
        id=collection["id"],
        name=collection["name"],
        description=collection["description"],
        visibility=collection["visibility"],
        items=[
            CollectionItemResponse(
                summaryId=item["summary_id"],
                summaryText=item["summary_text"],
                position=item["position"],
            )
            for item in items
        ],
    )


def update_collection_handler(
    collection_id: UUID,
    request: UpdateCollectionRequest,
    user_id: str,
    apps: AppManager,
) -> None:
    collection = apps.history_app.get_collection(collection_id=collection_id)
    if collection is None or collection["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Collection not found")
    updates = request.dict(exclude_none=True)
    if updates:
        apps.history_app.update_collection(collection_id=collection_id, **updates)


def delete_collection_handler(
    collection_id: UUID, user_id: str, apps: AppManager
) -> None:
    collection = apps.history_app.get_collection(collection_id=collection_id)
    if collection is None or collection["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Collection not found")
    apps.history_app.delete_collection(collection_id=collection_id)


def add_item_handler(
    collection_id: UUID,
    request: AddItemRequest,
    user_id: str,
    apps: AppManager,
) -> CollectionItemResponse:
    collection = apps.history_app.get_collection(collection_id=collection_id)
    if collection is None or collection["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Collection not found")
    position = apps.history_app.add_collection_item(
        collection_id=collection_id, summary_id=request.summaryId
    )
    return CollectionItemResponse(
        summaryId=request.summaryId, summaryText="", position=position
    )


def remove_item_handler(
    collection_id: UUID,
    summary_id: UUID,
    user_id: str,
    apps: AppManager,
) -> None:
    collection = apps.history_app.get_collection(collection_id=collection_id)
    if collection is None or collection["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Collection not found")
    apps.history_app.remove_collection_item(
        collection_id=collection_id, summary_id=summary_id
    )
