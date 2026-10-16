"""Marcações para excluir notas e itens dos relatórios.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notas", sa.Column("ignorada", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("itens", sa.Column("ignorado", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("itens") as batch:
        batch.drop_column("ignorado")
    with op.batch_alter_table("notas") as batch:
        batch.drop_column("ignorada")
