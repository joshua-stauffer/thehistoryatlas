"""add_pg_trgm_extension

Revision ID: 2024041501
Revises: 0516522b0380
Create Date: 2024-04-15 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "2024041501"
down_revision: Union[str, None] = "0516522b0380"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pg_trgm extension
    op.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

    # Create GIN index on names table for trigram-based search
    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_names_trgm_gin 
            ON names USING GIN (name gin_trgm_ops);
            """
        )
    )


def downgrade() -> None:
    # Drop the GIN index first
    op.execute(text("DROP INDEX IF EXISTS idx_names_trgm_gin;"))

    # Note: We don't drop the pg_trgm extension in downgrade as it might be used by other parts
    # of the application or other extensions. Dropping extensions can be dangerous.
    # If absolutely necessary, it can be dropped manually by the database administrator.
