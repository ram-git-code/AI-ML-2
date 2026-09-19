"""add PostgreSQL question embeddings

Revision ID: f4a1c9d8e2b3
Revises: d85594bdc8a7
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f4a1c9d8e2b3"
down_revision: Union[str, None] = "d85594bdc8a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("questions", sa.Column("embedding_model", sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "embedding_model")
    op.drop_column("questions", "embedding")