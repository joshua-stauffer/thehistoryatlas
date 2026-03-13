import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)


class ApiKeyRepository:
    def __init__(self, engine: Engine):
        self._engine = engine

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def create_api_key(self, user_id: str, name: str) -> tuple[str, dict]:
        """Create a new API key. Returns (raw_key, record_dict).
        The raw key is only available at creation time."""
        raw_key = secrets.token_urlsafe(48)
        key_hash = self._hash_key(raw_key)
        key_id = uuid4()
        now = datetime.now(timezone.utc)

        with Session(self._engine, future=True) as session:
            session.execute(
                text(
                    """
                    INSERT INTO api_keys (id, key_hash, user_id, name, created_at, is_active)
                    VALUES (:id, :key_hash, :user_id, :name, :created_at, true)
                    """
                ),
                {
                    "id": key_id,
                    "key_hash": key_hash,
                    "user_id": user_id,
                    "name": name,
                    "created_at": now,
                },
            )
            session.commit()

        record = {
            "id": key_id,
            "name": name,
            "user_id": user_id,
            "created_at": now,
        }
        return raw_key, record

    def validate_api_key(self, raw_key: str) -> Optional[str]:
        """Validate an API key. Returns user_id if valid, None otherwise."""
        key_hash = self._hash_key(raw_key)
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                    SELECT user_id, is_active FROM api_keys
                    WHERE key_hash = :key_hash
                    """
                ),
                {"key_hash": key_hash},
            ).one_or_none()

            if row is None or not row.is_active:
                return None

            # Update last_used_at
            session.execute(
                text(
                    """
                    UPDATE api_keys SET last_used_at = :now
                    WHERE key_hash = :key_hash
                    """
                ),
                {
                    "now": datetime.now(timezone.utc),
                    "key_hash": key_hash,
                },
            )
            session.commit()
            return row.user_id

    def deactivate_api_key(self, key_id: UUID, user_id: str) -> bool:
        """Deactivate an API key. Returns True if found and deactivated."""
        with Session(self._engine, future=True) as session:
            result = session.execute(
                text(
                    """
                    UPDATE api_keys SET is_active = false
                    WHERE id = :key_id AND user_id = :user_id
                    """
                ),
                {"key_id": key_id, "user_id": user_id},
            )
            session.commit()
            return result.rowcount > 0
