"""add_null_story_order_idx

Revision ID: 92543275eff2
Revises: 7241d695b706
Create Date: 2025-05-04 14:13:53.477942

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "92543275eff2"
down_revision: Union[str, None] = "7241d695b706"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a complementary index for tag_instances where story_order IS NULL
    # This will help queries that filter for NULL story_order values
    op.create_index(
        "idx_tag_instances_null_story_order",
        "tag_instances",
        ["tag_id"],
        unique=False,
        postgresql_where=sa.text("story_order IS NULL"),
    )


def downgrade() -> None:
    # Remove the index we added in the upgrade
    op.drop_index("idx_tag_instances_null_story_order", table_name="tag_instances")
