"""add_performance_indices

Revision ID: 0516522b0380
Revises: c1304797a996
Create Date: 2025-04-14 17:56:01.107703

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "0516522b0380"
down_revision: Union[str, None] = "c1304797a996"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These indices are already created in the baseline migration
    # This migration is a placeholder for future performance improvements

    # Run ANALYZE on tables to update statistics for the query planner
    op.execute(text("ANALYZE tags;"))
    op.execute(text("ANALYZE times;"))
    op.execute(text("ANALYZE tag_instances;"))
    op.execute(text("ANALYZE summaries;"))
    op.execute(text("ANALYZE citations;"))
    op.execute(text("ANALYZE tag_names;"))
    op.execute(text("ANALYZE places;"))


def downgrade() -> None:
    # No actions needed for downgrade as we're just analyzing tables
    pass
