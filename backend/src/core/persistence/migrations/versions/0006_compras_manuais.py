"""Compras e estabelecimentos sem dados fiscais.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("estabelecimentos") as batch:
        batch.alter_column("cnpj", existing_type=sa.String(14), nullable=True)
        batch.alter_column("razao_social", existing_type=sa.String(200), nullable=True)
    with op.batch_alter_table("notas") as batch:
        batch.add_column(sa.Column("origem", sa.String(10), nullable=False, server_default="sefaz"))
        for nome, tamanho in (("chave", 44), ("numero", 20), ("serie", 10), ("url_origem", 2048)):
            batch.alter_column(nome, existing_type=sa.String(tamanho), nullable=True)


def downgrade() -> None:
    # Não descarta compras manuais para voltar a um schema que exige dados fiscais.
    conexao = op.get_bind()
    if conexao.scalar(sa.text("SELECT COUNT(*) FROM notas WHERE origem = 'manual'")) or conexao.scalar(
        sa.text("SELECT COUNT(*) FROM estabelecimentos WHERE cnpj IS NULL OR razao_social IS NULL")
    ):
        raise RuntimeError("Existem registros manuais incompatíveis com a versão anterior.")
    with op.batch_alter_table("notas") as batch:
        batch.drop_column("origem")
        for nome, tamanho in (("chave", 44), ("numero", 20), ("serie", 10), ("url_origem", 2048)):
            batch.alter_column(nome, existing_type=sa.String(tamanho), nullable=False)
    with op.batch_alter_table("estabelecimentos") as batch:
        batch.alter_column("cnpj", existing_type=sa.String(14), nullable=False)
        batch.alter_column("razao_social", existing_type=sa.String(200), nullable=False)
