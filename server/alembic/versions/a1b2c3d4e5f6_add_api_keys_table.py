"""add_api_keys_table

Revision ID: a1b2c3d4e5f6
Revises: f8a3c2e91d47
Create Date: 2026-03-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, TIMESTAMP, BOOLEAN

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8a3c2e91d47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key_hash", VARCHAR, nullable=False, unique=True),
        sa.Column(
            "user_id",
            VARCHAR,
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", VARCHAR, nullable=False),
        sa.Column(
            "created_at",
            TIMESTAMP,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_used_at", TIMESTAMP, nullable=True),
        sa.Column(
            "is_active",
            BOOLEAN,
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])


def downgrade() -> None:
    op.drop_index("idx_api_keys_key_hash")
    op.drop_table("api_keys")
