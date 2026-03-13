from uuid import UUID

from fastapi import HTTPException

from the_history_atlas.api.types.api_keys import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    DeactivateApiKeyResponse,
)
from the_history_atlas.apps.app_manager import AppManager


def create_api_key_handler(
    apps: AppManager, request: CreateApiKeyRequest, user_id: str
) -> CreateApiKeyResponse:
    raw_key, record = apps.accounts_app.create_api_key(
        user_id=user_id, name=request.name
    )
    return CreateApiKeyResponse(
        id=record["id"],
        name=record["name"],
        raw_key=raw_key,
        created_at=record["created_at"],
    )


def deactivate_api_key_handler(
    apps: AppManager, key_id: UUID, user_id: str
) -> DeactivateApiKeyResponse:
    success = apps.accounts_app.deactivate_api_key(key_id=key_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return DeactivateApiKeyResponse(success=True)
