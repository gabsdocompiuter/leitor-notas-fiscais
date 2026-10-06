"""Conteúdo das embalagens de produtos contados em unidades.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("itens", sa.Column("quantidade_pacotes", sa.Text(), nullable=True))
    op.add_column("itens", sa.Column("unidades_por_pacote", sa.Text(), nullable=True))
    op.add_column("associacoes_produto", sa.Column("unidades_por_pacote", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("associacoes_produto") as batch:
        batch.drop_column("unidades_por_pacote")
    with op.batch_alter_table("itens") as batch:
        batch.drop_column("unidades_por_pacote")
        batch.drop_column("quantidade_pacotes")
