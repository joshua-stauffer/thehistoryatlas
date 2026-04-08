"""make_story_order_nullable

Revision ID: ecb1ae009136
Revises: a68f7c2c57d9
Create Date: 2025-04-17 12:54:42.820672

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ecb1ae009136"
down_revision: Union[str, None] = "a68f7c2c57d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter the tag_instances table to make story_order nullable
    op.alter_column(
        "tag_instances", "story_order", existing_type=sa.INTEGER(), nullable=True
    )


def downgrade() -> None:
    # Restore the not-null constraint
    op.alter_column(
        "tag_instances", "story_order", existing_type=sa.INTEGER(), nullable=False
    )
