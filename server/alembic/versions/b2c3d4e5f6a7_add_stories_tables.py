"""add_stories_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, VARCHAR, TIMESTAMP, INTEGER

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", VARCHAR, nullable=False),
        sa.Column("description", VARCHAR, nullable=True),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sources.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            TIMESTAMP,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_stories_source_id", "stories", ["source_id"])

    op.create_table(
        "story_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "story_id",
            UUID(as_uuid=True),
            sa.ForeignKey("stories.id"),
            nullable=False,
        ),
        sa.Column(
            "summary_id",
            UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=False,
        ),
        sa.Column("position", INTEGER, nullable=False),
        sa.UniqueConstraint("story_id", "summary_id", name="uq_story_summary"),
        sa.UniqueConstraint("story_id", "position", name="uq_story_position"),
    )


def downgrade() -> None:
    op.drop_table("story_summaries")
    op.drop_index("idx_stories_source_id")
    op.drop_table("stories")
