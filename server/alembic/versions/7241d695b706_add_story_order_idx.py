"""add_story_order_idx

Revision ID: 7241d695b706
Revises: 426d313ef4c5
Create Date: 2025-05-04 13:49:44.636419

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7241d695b706"
down_revision: Union[str, None] = "426d313ef4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a dedicated index for the story_order column to improve MAX(story_order) queries
    op.create_index(
        "idx_tag_instances_story_order",
        "tag_instances",
        ["story_order"],
        unique=False,
        postgresql_where=sa.text("story_order IS NOT NULL"),
    )


def downgrade() -> None:
    # Remove the index added in the upgrade
    op.drop_index("idx_tag_instances_story_order", table_name="tag_instances")
