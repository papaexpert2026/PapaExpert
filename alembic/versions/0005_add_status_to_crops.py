"""add optional status to crops

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: los cultivos ya registrados quedan con status = NULL,
    # la app lo trata como "sin especificar".
    op.add_column("crops", sa.Column("status", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("crops", "status")
