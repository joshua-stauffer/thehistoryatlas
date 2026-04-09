"""Add user collections tables

Revision ID: c6d7e8f9a0b1
Revises: b5d6e7f8a9c0
Create Date: 2026-04-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "c6d7e8f9a0b1"
down_revision = "b5d6e7f8a9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_collections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.VARCHAR, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.VARCHAR, nullable=False),
        sa.Column("description", sa.VARCHAR, nullable=True),
        sa.Column(
            "visibility",
            sa.VARCHAR,
            nullable=False,
            server_default="private",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_user_collections_user_id", "user_collections", ["user_id"]
    )

    op.create_table(
        "user_collection_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "collection_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user_collections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "summary_id",
            UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=False,
        ),
        sa.Column("position", sa.INTEGER, nullable=False),
        sa.Column(
            "added_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "collection_id", "summary_id", name="uq_collection_item"
        ),
        sa.UniqueConstraint(
            "collection_id", "position", name="uq_collection_position"
        ),
    )
    op.create_index(
        "idx_collection_items_collection_id",
        "user_collection_items",
        ["collection_id"],
    )


def downgrade() -> None:
    op.drop_table("user_collection_items")
    op.drop_index(
        "idx_user_collections_user_id", table_name="user_collections"
    )
    op.drop_table("user_collections")
