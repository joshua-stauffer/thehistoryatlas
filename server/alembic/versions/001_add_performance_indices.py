"""Add performance indices

Revision ID: 001_add_performance_indices
Revises:
Create Date: 2024-06-26

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_add_performance_indices"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index for faster lookup of tags by wikidata_id (used in get_tags_by_wikidata_ids)
    op.create_index(
        "idx_tags_wikidata_id",
        "tags",
        ["wikidata_id"],
        postgresql_where=sa.text("wikidata_id IS NOT NULL"),
    )

    # Composite index for time_exists method
    op.create_index(
        "idx_times_lookup", "times", ["datetime", "calendar_model", "precision"]
    )

    # Index for tag instances by tag_id and story_order for faster sorting
    op.create_index(
        "idx_tag_instances_tag_id_story_order",
        "tag_instances",
        ["tag_id", "story_order"],
    )

    # Index for summaries by text for faster lookups
    op.create_index(
        "idx_summaries_text", "summaries", ["text"], postgresql_using="hash"
    )

    # Index for citations by summary_id
    op.create_index("idx_citations_summary_id", "citations", ["summary_id"])

    # Index for tag_names lookup
    op.create_index("idx_tag_names_composite", "tag_names", ["tag_id", "name_id"])

    # Time-related indices for faster related story lookups
    op.create_index("idx_times_datetime", "times", ["datetime"])

    # Index for place coordinates
    op.create_index(
        "idx_places_coordinates",
        "places",
        ["latitude", "longitude"],
        postgresql_where=sa.text("latitude IS NOT NULL AND longitude IS NOT NULL"),
    )


def downgrade() -> None:
    # Drop all indices in reverse order
    op.drop_index("idx_places_coordinates", table_name="places")
    op.drop_index("idx_times_datetime", table_name="times")
    op.drop_index("idx_tag_names_composite", table_name="tag_names")
    op.drop_index("idx_citations_summary_id", table_name="citations")
    op.drop_index("idx_summaries_text", table_name="summaries")
    op.drop_index("idx_tag_instances_tag_id_story_order", table_name="tag_instances")
    op.drop_index("idx_times_lookup", table_name="times")
    op.drop_index("idx_tags_wikidata_id", table_name="tags")
