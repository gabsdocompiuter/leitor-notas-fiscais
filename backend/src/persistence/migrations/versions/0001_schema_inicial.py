"""Schema inicial SQLAlchemy.

Revision ID: 0001
Revises: None
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from src.persistence.types import DecimalText, StringList

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(100, collation="NOCASE"), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "estabelecimentos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column("razao_social", sa.String(200), nullable=False),
        sa.Column("apelido", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("cnpj"),
    )
    op.create_table(
        "marcas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(100, collation="NOCASE"), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "produtos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(150, collation="NOCASE"), nullable=False),
        sa.Column("categoria_id", sa.Uuid(), nullable=False),
        sa.Column("nao_solicitar_marca", sa.Boolean(), nullable=False),
        sa.Column("tratar_apenas_como_unidades", sa.Boolean(), nullable=False),
        sa.Column("contem_variacoes", sa.Boolean(), nullable=False),
        sa.Column("unidade_medida", sa.Enum("KG", "G", "L", "ML", name="unidademedida"), nullable=True),
        sa.CheckConstraint(
            "(tratar_apenas_como_unidades = 1 AND contem_variacoes = 0 AND unidade_medida IS NULL) "
            "OR (tratar_apenas_como_unidades = 0 AND unidade_medida IS NOT NULL)",
            name="ck_produto_tipo",
        ),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome", "categoria_id", name="uq_produto_nome_categoria"),
    )
    op.create_table(
        "apresentacoes_produto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("produto_id", sa.Uuid(), nullable=False),
        sa.Column("marca_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["marca_id"], ["marcas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_apresentacao_produto_marca", "apresentacoes_produto", ["produto_id", "marca_id"], unique=True)
    op.create_table(
        "variacoes_produto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("produto_id", sa.Uuid(), nullable=False),
        sa.Column("quantidade", DecimalText(), nullable=False),
        sa.Column("unidade_medida", sa.Enum("KG", "G", "L", "ML", name="unidademedida"), nullable=False),
        sa.Column("descricao", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("produto_id", "quantidade", "unidade_medida", name="uq_variacao_produto"),
    )
    op.create_table(
        "notas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chave", sa.String(44), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("serie", sa.String(10), nullable=False),
        sa.Column("estabelecimento_id", sa.Uuid(), nullable=False),
        sa.Column("emissao", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantidade_itens", sa.Integer(), nullable=False),
        sa.Column("valor_total", DecimalText(), nullable=False),
        sa.Column("desconto", DecimalText(), nullable=False),
        sa.Column("valor_a_pagar", DecimalText(), nullable=False),
        sa.Column("url_origem", sa.String(2048), nullable=False),
        sa.Column("situacao", sa.Enum("lida", "em_revisao", "importada", name="situacaonota"), nullable=False),
        sa.Column("importada_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("chave"),
    )
    op.create_index("idx_notas_emissao", "notas", ["emissao"])
    op.create_table(
        "itens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nota_id", sa.Uuid(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(100), nullable=False),
        sa.Column("descricao_original", sa.String(500), nullable=False),
        sa.Column("quantidade", DecimalText(), nullable=False),
        sa.Column("unidade_original", sa.String(20), nullable=False),
        sa.Column("valor_unitario", DecimalText(), nullable=False),
        sa.Column("valor_total", DecimalText(), nullable=False),
        sa.Column("alertas", StringList(), nullable=False),
        sa.Column("apresentacao_id", sa.Uuid(), nullable=True),
        sa.Column("variacao_id", sa.Uuid(), nullable=True),
        sa.Column("quantidade_confirmada", DecimalText(), nullable=True),
        sa.Column("revisado", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["apresentacao_id"], ["apresentacoes_produto.id"]),
        sa.ForeignKeyConstraint(["nota_id"], ["notas.id"]),
        sa.ForeignKeyConstraint(["variacao_id"], ["variacoes_produto.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nota_id", "numero", name="uq_item_nota_numero"),
    )
    op.create_table(
        "leituras",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chave", sa.String(44), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("nota_id", sa.Uuid(), nullable=True),
        sa.Column("erro_consulta", sa.String(1000), nullable=True),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["nota_id"], ["notas.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("chave"),
    )
    op.create_table(
        "associacoes_produto",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("estabelecimento_id", sa.Uuid(), nullable=False),
        sa.Column("codigo_item", sa.String(100), nullable=False),
        sa.Column("descricao_original", sa.String(500), nullable=False),
        sa.Column("descricao_normalizada", sa.String(500), nullable=False),
        sa.Column("apresentacao_id", sa.Uuid(), nullable=False),
        sa.Column("variacao_id", sa.Uuid(), nullable=True),
        sa.Column("fator_conversao", DecimalText(), nullable=False),
        sa.ForeignKeyConstraint(["apresentacao_id"], ["apresentacoes_produto.id"]),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"]),
        sa.ForeignKeyConstraint(["variacao_id"], ["variacoes_produto.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estabelecimento_id", "codigo_item", name="uq_associacao_estabelecimento_codigo"),
    )
    op.create_index("idx_associacoes_descricao", "associacoes_produto", ["descricao_normalizada"])


def downgrade() -> None:
    for tabela in (
        "associacoes_produto", "leituras", "itens", "notas",
        "variacoes_produto", "apresentacoes_produto", "produtos",
        "marcas", "estabelecimentos", "categorias",
    ):
        op.drop_table(tabela)
