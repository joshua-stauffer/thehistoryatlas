"""add_index_to_tag_instances_summary_id

Revision ID: 426d313ef4c5
Revises: 1497a8d4df27
Create Date: 2025-05-04 13:33:30.442936

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "426d313ef4c5"
down_revision: Union[str, None] = "1497a8d4df27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_tag_instances_summary_id",
        "tag_instances",
        ["summary_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_tag_instances_summary_id", table_name="tag_instances")
