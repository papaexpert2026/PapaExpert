"""make chat_sessions.detection_id nullable (support general assistant chat)

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Permite crear sesiones de chat "generales" (sin detección asociada),
    # para el Asistente IA accesible desde el menú sin partir de un
    # diagnóstico concreto. Las sesiones existentes (todas con detection_id)
    # no se ven afectadas ni se pierden.
    with op.batch_alter_table("chat_sessions") as batch_op:
        batch_op.alter_column("detection_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch_op:
        batch_op.alter_column("detection_id", existing_type=sa.Integer(), nullable=False)