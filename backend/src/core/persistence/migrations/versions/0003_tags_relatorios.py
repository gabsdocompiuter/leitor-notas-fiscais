"""Tags por item e opção de considerar a nota no mês seguinte.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notas", sa.Column(
        "considerar_proximo_mes", sa.Boolean(), nullable=False, server_default=sa.false()
    ))
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("nome_normalizado", sa.String(200), nullable=False, unique=True),
    )
    op.create_table(
        "itens_tags",
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("itens.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Uuid(), sa.ForeignKey("tags.id"), primary_key=True),
    )
    op.create_index("idx_itens_tags_tag", "itens_tags", ["tag_id"])


def downgrade() -> None:
    op.drop_index("idx_itens_tags_tag", table_name="itens_tags")
    op.drop_table("itens_tags")
    op.drop_table("tags")
    with op.batch_alter_table("notas") as batch:
        batch.drop_column("considerar_proximo_mes")
