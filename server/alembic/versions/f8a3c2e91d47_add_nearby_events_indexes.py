"""add_nearby_events_indexes

Revision ID: f8a3c2e91d47
Revises: 0deb2c3901a6
Create Date: 2026-03-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "f8a3c2e91d47"
down_revision: Union[str, None] = "0deb2c3901a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for the nearby-events WHERE clause.
    # Column order: equality first (calendar_model), then prefix-LIKE (datetime with
    # text_pattern_ops so LIKE 'prefix%' uses the index), then spatial ranges.
    op.execute(
        text(
            "CREATE INDEX idx_summaries_nearby "
            "ON summaries (calendar_model, datetime text_pattern_ops, latitude, longitude);"
        )
    )

    # story_names is LEFT JOINed on tag_id but has no index, causing a full table scan
    # for every person tag resolved by the query.
    op.execute(text("CREATE INDEX idx_story_names_tag_id ON story_names (tag_id);"))


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS idx_summaries_nearby;"))
    op.execute(text("DROP INDEX IF EXISTS idx_story_names_tag_id;"))
