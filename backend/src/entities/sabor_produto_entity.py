from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..core.persistence.base_entity import BaseEntity


class SaborProdutoEntity(BaseEntity):
    __tablename__ = "sabores_produto"
    __table_args__ = (UniqueConstraint("produto_id", "nome", name="uq_sabor_produto"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    produto_id: Mapped[UUID] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(100, collation="NOCASE"))
