"""Add pgvector extension and embedding column to summaries

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-04-09

Prerequisites:
    pgvector must be installed on the PostgreSQL server before running.
    - macOS (Homebrew): brew install pgvector
    - Ubuntu/Debian: apt install postgresql-16-pgvector
    - Docker: use pgvector/pgvector:pg16 image
    - From source: https://github.com/pgvector/pgvector#installation
"""
from alembic import op
import sqlalchemy as sa

revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "ALTER TABLE summaries ADD COLUMN embedding vector(1536)"
    )
    # After backfilling embeddings, create the IVFFlat index:
    #   CREATE INDEX CONCURRENTLY idx_summaries_embedding
    #   ON summaries USING ivfflat (embedding vector_cosine_ops)
    #   WITH (lists = 100);


def downgrade() -> None:
    op.execute("ALTER TABLE summaries DROP COLUMN IF EXISTS embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
