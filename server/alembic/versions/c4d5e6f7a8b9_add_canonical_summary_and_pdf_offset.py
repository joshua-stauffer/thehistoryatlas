"""Add canonical_summary_id to summaries and pdf_page_offset to sources

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-03-21

"""

from typing import Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Self-referential FK: marks a summary as a duplicate of an existing one.
    # NULL means this is a canonical (first-seen) summary.
    op.add_column(
        "summaries",
        sa.Column(
            "canonical_summary_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=True,
        ),
    )

    # Offset between PDF page numbers and printed book page numbers.
    # book_page = citations.page_num - sources.pdf_page_offset
    op.add_column(
        "sources",
        sa.Column(
            "pdf_page_offset",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("summaries", "canonical_summary_id")
    op.drop_column("sources", "pdf_page_offset")
