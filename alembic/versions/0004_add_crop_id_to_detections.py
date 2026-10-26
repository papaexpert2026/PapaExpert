"""add nullable crop_id to detections

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable a propósito: no se pierde ni se rompe ningún diagnóstico
    # existente, que simplemente queda con crop_id = NULL.
    # Se usa batch_alter_table para que la migración funcione tanto en
    # PostgreSQL (producción) como en SQLite (usado solo en pruebas locales).
    with op.batch_alter_table("detections") as batch_op:
        batch_op.add_column(sa.Column("crop_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_detections_crop_id_crops",
            "crops",
            ["crop_id"],
            ["id"],
        )
        batch_op.create_index("ix_detections_crop_id", ["crop_id"])


def downgrade() -> None:
    with op.batch_alter_table("detections") as batch_op:
        batch_op.drop_index("ix_detections_crop_id")
        batch_op.drop_constraint("fk_detections_crop_id_crops", type_="foreignkey")
        batch_op.drop_column("crop_id")
