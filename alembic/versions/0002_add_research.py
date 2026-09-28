"""add research_cache table and sources_json to chat_messages

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("sources_json", sa.Text(), nullable=True))

    op.create_table(
        "research_cache",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("disease", sa.String(length=150), nullable=False, unique=True, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("research_cache")
    op.drop_column("chat_messages", "sources_json")
