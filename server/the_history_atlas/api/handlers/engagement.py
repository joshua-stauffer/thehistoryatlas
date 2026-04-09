import logging
from uuid import UUID

from fastapi import HTTPException

from the_history_atlas.api.types.engagement import (
    SignupRequest,
    SignupResponse,
    FavoriteResponse,
    FavoriteListResponse,
    FavoriteListItem,
)
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.accounts.errors import DuplicateUsernameError

log = logging.getLogger(__name__)


def signup_handler(request: SignupRequest, apps: AppManager) -> SignupResponse:
    """Self-service account creation."""
    try:
        token = apps.accounts_app.signup(
            username=request.username,
            password=request.password,
            email=request.email,
            first_name=request.firstName,
            last_name=request.lastName,
        )
    except DuplicateUsernameError:
        raise HTTPException(
            status_code=409,
            detail="Username already taken",
        )
    return SignupResponse(accessToken=token)


def add_favorite_handler(
    summary_id: UUID, user_id: str, apps: AppManager
) -> FavoriteResponse:
    apps.history_app.add_favorite(user_id=user_id, summary_id=summary_id)
    return FavoriteResponse(
        userId=user_id, summaryId=summary_id, favorited=True
    )


def remove_favorite_handler(
    summary_id: UUID, user_id: str, apps: AppManager
) -> FavoriteResponse:
    apps.history_app.remove_favorite(user_id=user_id, summary_id=summary_id)
    return FavoriteResponse(
        userId=user_id, summaryId=summary_id, favorited=False
    )


def list_favorites_handler(
    user_id: str, apps: AppManager
) -> FavoriteListResponse:
    favorites = apps.history_app.get_favorites(user_id=user_id)
    return FavoriteListResponse(
        favorites=[
            FavoriteListItem(
                summaryId=f["summary_id"],
                summaryText=f["summary_text"],
                createdAt=f["created_at"],
            )
            for f in favorites
        ]
    )


def record_view_handler(
    summary_id: UUID, user_id: str, apps: AppManager
) -> None:
    apps.history_app.record_view(user_id=user_id, summary_id=summary_id)
