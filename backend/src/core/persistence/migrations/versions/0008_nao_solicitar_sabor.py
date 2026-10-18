"""Permite ocultar a seleção de sabor por produto."""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("produtos", sa.Column("nao_solicitar_sabor", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("produtos") as batch:
        batch.drop_column("nao_solicitar_sabor")
