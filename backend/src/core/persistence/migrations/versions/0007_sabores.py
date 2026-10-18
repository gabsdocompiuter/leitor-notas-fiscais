"""Adiciona estrutura de sabores, sem reclassificar produtos ou itens existentes."""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("sabores_produto",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("produto_id", sa.Uuid(), sa.ForeignKey("produtos.id"), nullable=False),
        sa.Column("nome", sa.String(100, collation="NOCASE"), nullable=False),
        sa.UniqueConstraint("produto_id", "nome", name="uq_sabor_produto"),
    )
    for tabela in ("itens", "associacoes_produto"):
        with op.batch_alter_table(tabela) as batch:
            batch.add_column(sa.Column("sabor_id", sa.Uuid(), nullable=True))
            batch.create_foreign_key(f"fk_{tabela}_sabor", "sabores_produto", ["sabor_id"], ["id"])


def downgrade():
    for tabela in ("associacoes_produto", "itens"):
        with op.batch_alter_table(tabela) as batch:
            batch.drop_constraint(f"fk_{tabela}_sabor", type_="foreignkey")
            batch.drop_column("sabor_id")
    op.drop_table("sabores_produto")
