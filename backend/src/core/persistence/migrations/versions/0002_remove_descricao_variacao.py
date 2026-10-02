"""Remove a descrição livre das variações.

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("variacoes_produto") as batch_op:
        batch_op.drop_column("descricao")


def downgrade() -> None:
    with op.batch_alter_table("variacoes_produto") as batch_op:
        batch_op.add_column(sa.Column("descricao", sa.String(100), nullable=True))
