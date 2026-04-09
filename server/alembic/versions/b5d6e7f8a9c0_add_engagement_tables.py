"""Add user engagement tables (favorites, events, preferences)

Revision ID: b5d6e7f8a9c0
Revises: a3f8b1c2d9e4
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "b5d6e7f8a9c0"
down_revision = "a3f8b1c2d9e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User favorites — bookmarked events
    op.create_table(
        "user_favorites",
        sa.Column("user_id", sa.VARCHAR, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "summary_id",
            UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "summary_id", name="uq_user_favorite"),
    )
    op.create_index(
        "idx_user_favorites_user_id", "user_favorites", ["user_id"]
    )

    # User events — append-only interaction log
    op.create_table(
        "user_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.VARCHAR, nullable=False),
        sa.Column(
            "summary_id",
            UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.VARCHAR, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_user_events_user_created",
        "user_events",
        ["user_id", "created_at"],
    )

    # User theme preferences — materialized from behavior
    op.create_table(
        "user_theme_preferences",
        sa.Column("user_id", sa.VARCHAR, nullable=False),
        sa.Column(
            "theme_id",
            UUID(as_uuid=True),
            sa.ForeignKey("themes.id"),
            nullable=False,
        ),
        sa.Column("score", sa.FLOAT, nullable=False, server_default="0.0"),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP,
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "theme_id"),
    )


def downgrade() -> None:
    op.drop_table("user_theme_preferences")
    op.drop_table("user_events")
    op.drop_index("idx_user_favorites_user_id", table_name="user_favorites")
    op.drop_table("user_favorites")
