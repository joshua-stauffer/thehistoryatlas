"""add_datetime_location_to_summaries

Revision ID: e4f7a2d6b159
Revises: 92543275eff2
Create Date: 2025-05-20 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e4f7a2d6b159"
down_revision: Union[str, None] = "92543275eff2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add datetime, calendar_model, precision, latitude, and longitude columns to summaries table
    op.add_column("summaries", sa.Column("datetime", sa.VARCHAR(), nullable=True))
    op.add_column("summaries", sa.Column("calendar_model", sa.VARCHAR(), nullable=True))
    op.add_column("summaries", sa.Column("precision", sa.INTEGER(), nullable=True))
    op.add_column("summaries", sa.Column("latitude", sa.FLOAT(), nullable=True))
    op.add_column("summaries", sa.Column("longitude", sa.FLOAT(), nullable=True))

    # Add indices for columns that will be used in expensive queries
    op.create_index("idx_summaries_datetime", "summaries", ["datetime"], unique=False)
    op.create_index("idx_summaries_latitude", "summaries", ["latitude"], unique=False)
    op.create_index("idx_summaries_longitude", "summaries", ["longitude"], unique=False)


def downgrade() -> None:
    # Drop indices first
    op.drop_index("idx_summaries_datetime", table_name="summaries")
    op.drop_index("idx_summaries_latitude", table_name="summaries")
    op.drop_index("idx_summaries_longitude", table_name="summaries")

    # Then drop columns
    op.drop_column("summaries", "longitude")
    op.drop_column("summaries", "latitude")
    op.drop_column("summaries", "precision")
    op.drop_column("summaries", "calendar_model")
    op.drop_column("summaries", "datetime")
