from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateApiKeyRequest(BaseModel):
    name: str


class CreateApiKeyResponse(BaseModel):
    id: UUID
    name: str
    raw_key: str
    created_at: datetime


class DeactivateApiKeyResponse(BaseModel):
    success: bool
