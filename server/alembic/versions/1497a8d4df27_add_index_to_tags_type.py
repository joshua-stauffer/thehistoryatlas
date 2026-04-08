"""add_index_to_tags_type

Revision ID: 1497a8d4df27
Revises: ecb1ae009136
Create Date: 2025-05-04 13:25:08.370767

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1497a8d4df27"
down_revision: Union[str, None] = "ecb1ae009136"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_tags_type", "tags", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_tags_type", table_name="tags")
