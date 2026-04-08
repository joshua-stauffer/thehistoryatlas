"""add_themes_tables

Revision ID: a3f8b1c2d9e4
Revises: b2c3d4e5f6a7
Create Date: 2026-03-20 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a3f8b1c2d9e4"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fixed theme taxonomy — slugs are stable identifiers used in code and APIs.
# Top-level categories exist for UI grouping (theme filter chips).
# Subcategories are the actual tags assigned to events. They are flat and
# co-occurring: an event can have 1-3 subcategory tags across any categories
# (e.g. the Gutenberg press: invention-and-engineering + literature).
_CATEGORIES = [
    # (name, slug, display_order)
    ("Arts & Culture", "arts-and-culture", 10),
    ("Science & Technology", "science-and-technology", 20),
    ("Politics & Power", "politics-and-power", 30),
    ("Society", "society", 40),
    ("Daily Life", "daily-life", 50),
]

_SUBCATEGORIES = [
    # (name, slug, parent_slug, display_order)
    # -- Arts & Culture
    ("Music", "music", "arts-and-culture", 11),
    ("Visual Arts", "visual-arts", "arts-and-culture", 12),
    ("Literature", "literature", "arts-and-culture", 13),
    ("Theater & Film", "theater-and-film", "arts-and-culture", 14),
    ("Architecture", "architecture", "arts-and-culture", 15),
    ("Fashion & Design", "fashion-and-design", "arts-and-culture", 16),
    # -- Science & Technology
    ("Astronomy & Space", "astronomy-and-space", "science-and-technology", 21),
    ("Natural Science", "natural-science", "science-and-technology", 22),
    ("Medicine", "medicine", "science-and-technology", 23),
    ("Invention & Engineering", "invention-and-engineering", "science-and-technology", 24),
    ("Mathematics", "mathematics", "science-and-technology", 25),
    ("Exploration & Navigation", "exploration-and-navigation", "science-and-technology", 26),
    # -- Politics & Power
    ("War & Conflict", "war-and-conflict", "politics-and-power", 31),
    ("Diplomacy", "diplomacy", "politics-and-power", 32),
    ("Governance", "governance", "politics-and-power", 33),
    ("Revolution", "revolution", "politics-and-power", 34),
    ("Royalty & Dynasty", "royalty-and-dynasty", "politics-and-power", 35),
    ("Espionage & Intelligence", "espionage-and-intelligence", "politics-and-power", 36),
    # -- Society
    ("Religion", "religion", "society", 41),
    ("Education", "education", "society", 42),
    ("Philosophy & Ideas", "philosophy-and-ideas", "society", 43),
    ("Social Movement", "social-movement", "society", 44),
    ("Economics & Trade", "economics-and-trade", "society", 45),
    ("Crime & Justice", "crime-and-justice", "society", 46),
    # -- Daily Life
    ("Food & Cuisine", "food-and-cuisine", "daily-life", 51),
    ("Sports & Athletics", "sports-and-athletics", "daily-life", 52),
    ("Love & Relationships", "love-and-relationships", "daily-life", 53),
    ("Migration", "migration", "daily-life", 54),
    ("Customs & Traditions", "customs-and-traditions", "daily-life", 55),
]


def upgrade() -> None:
    themes_table = op.create_table(
        "themes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), nullable=False, unique=True),
        sa.Column("slug", sa.VARCHAR(), nullable=False, unique=True),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("themes.id"),
            nullable=True,
        ),
        sa.Column("display_order", sa.INTEGER(), nullable=False),
    )
    op.create_index("idx_themes_parent_id", "themes", ["parent_id"])

    op.create_table(
        "summary_themes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "summary_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("summaries.id"),
            nullable=False,
        ),
        sa.Column(
            "theme_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("themes.id"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, default=False),
        sa.Column("confidence", sa.FLOAT(), nullable=True),
        sa.UniqueConstraint("summary_id", "theme_id", name="uq_summary_theme"),
    )
    op.create_index("idx_summary_themes_summary_id", "summary_themes", ["summary_id"])
    op.create_index("idx_summary_themes_theme_id", "summary_themes", ["theme_id"])

    # Seed top-level categories first, collecting id by slug for parent lookups.
    slug_to_id: dict[str, str] = {}
    category_rows = []
    for name, slug, display_order in _CATEGORIES:
        theme_id = str(uuid4())
        slug_to_id[slug] = theme_id
        category_rows.append(
            {
                "id": theme_id,
                "name": name,
                "slug": slug,
                "parent_id": None,
                "display_order": display_order,
            }
        )
    op.bulk_insert(themes_table, category_rows)

    # Seed subcategories with parent_id resolved from slug_to_id.
    subcategory_rows = []
    for name, slug, parent_slug, display_order in _SUBCATEGORIES:
        theme_id = str(uuid4())
        slug_to_id[slug] = theme_id
        subcategory_rows.append(
            {
                "id": theme_id,
                "name": name,
                "slug": slug,
                "parent_id": slug_to_id[parent_slug],
                "display_order": display_order,
            }
        )
    op.bulk_insert(themes_table, subcategory_rows)


def downgrade() -> None:
    op.drop_index("idx_summary_themes_theme_id", table_name="summary_themes")
    op.drop_index("idx_summary_themes_summary_id", table_name="summary_themes")
    op.drop_table("summary_themes")
    op.drop_index("idx_themes_parent_id", table_name="themes")
    op.drop_table("themes")
