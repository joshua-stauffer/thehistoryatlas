from uuid import UUID

from pydantic import BaseModel


class SignupRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    firstName: str | None = None
    lastName: str | None = None


class SignupResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"


class FavoriteResponse(BaseModel):
    userId: str
    summaryId: UUID
    favorited: bool


class FavoriteListItem(BaseModel):
    summaryId: UUID
    summaryText: str
    createdAt: str


class FavoriteListResponse(BaseModel):
    favorites: list[FavoriteListItem]


class ViewEventRequest(BaseModel):
    userId: str | None = None
